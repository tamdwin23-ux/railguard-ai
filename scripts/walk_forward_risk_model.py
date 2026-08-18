import pandas as pd
import numpy as np
import joblib

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

DATA_FILE = "data/features_v2/metropt_features_trend_30min.csv"
MODEL_DIR = "models/risk"
RESULT_FILE = "results/risk/logistic_walk_forward.csv"

SENSORS = [
    "TP2",
    "TP3",
    "H1",
    "DV_pressure",
    "Reservoirs",
    "Oil_temperature",
    "Motor_current",
]

FEATURES = []

for sensor in SENSORS:
    FEATURES.extend([
        f"{sensor}_mean",
        f"{sensor}_mean_30m_mean",
        f"{sensor}_mean_30m_std",
        f"{sensor}_mean_vs_30m_mean",
    ])

FOLDS = {
    "F2": pd.Timestamp("2020-05-29 23:30:00"),
    "F3": pd.Timestamp("2020-06-05 10:00:00"),
    "F4": pd.Timestamp("2020-07-15 14:30:00"),
}

USECOLS = [
    "window_start",
    "is_failure",
    "failure_within_2h",
] + FEATURES


def load_fold(failure_start):
    warning_start = failure_start - pd.Timedelta(hours=2)
    test_start = warning_start - pd.Timedelta(days=7)

    train_positive = []
    train_negative = []
    test_parts = []

    for chunk in pd.read_csv(
        DATA_FILE,
        usecols=USECOLS,
        chunksize=50000,
        parse_dates=["window_start"],
    ):
        # Training only uses historical data.
        historical = chunk[
            chunk["window_start"] < warning_start
        ]

        positive = historical[
            (historical["failure_within_2h"] == 1)
            & (historical["is_failure"] == 0)
        ]

        negative = historical[
            (historical["failure_within_2h"] == 0)
            & (historical["is_failure"] == 0)
        ]

        if not positive.empty:
            train_positive.append(positive)

        # Sample normal windows to keep EC2 memory usage low.
        if not negative.empty:
            sample_n = min(3000, len(negative))

            train_negative.append(
                negative.sample(
                    n=sample_n,
                    random_state=42,
                )
            )

        # Future test interval.
        test = chunk[
            (chunk["window_start"] >= test_start)
            & (chunk["window_start"] < failure_start)
            & (chunk["is_failure"] == 0)
        ].copy()

        if not test.empty:
            # Keep only the CURRENT event's 2-hour warning
            # or true normal windows.
            current_warning = (
                (test["window_start"] >= warning_start)
                & (test["window_start"] < failure_start)
            )

            normal = test["failure_within_2h"] == 0

            test = test[current_warning | normal].copy()

            # Rebuild target specifically for this event.
            test["target"] = current_warning.astype(int)

            test_parts.append(test)

    positives = pd.concat(
        train_positive,
        ignore_index=True
    )

    negatives = pd.concat(
        train_negative,
        ignore_index=True
    )

    train = pd.concat(
        [positives, negatives],
        ignore_index=True
    )

    train["target"] = train[
        "failure_within_2h"
    ].astype(int)

    test = pd.concat(
        test_parts,
        ignore_index=True
    )

    return train, test


results = []

for fold_name, failure_start in FOLDS.items():

    print("\n====================")
    print("Testing:", fold_name)
    print("====================")

    train, test = load_fold(failure_start)

    X_train = train[FEATURES]
    y_train = train["target"]

    X_test = test[FEATURES]
    y_test = test["target"]

    print("Training positives:", int(y_train.sum()))
    print("Training negatives:", int((y_train == 0).sum()))
    print("Test pre-failure:", int(y_test.sum()))
    print("Test normal:", int((y_test == 0).sum()))

    pipeline = Pipeline([
        (
            "scaler",
            StandardScaler()
        ),
        (
            "model",
            LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                random_state=42,
            )
        ),
    ])

    pipeline.fit(X_train, y_train)

    train_scores = pipeline.predict_proba(
        X_train
    )[:, 1]

    train_normal_scores = train_scores[
        y_train.to_numpy() == 0
    ]

    # Alarm threshold based only on historical normal data.
    threshold = np.quantile(
        train_normal_scores,
        0.99
    )

    test_scores = pipeline.predict_proba(
        X_test
    )[:, 1]

    predictions = (
        test_scores >= threshold
    ).astype(int)

    normal_mask = y_test.to_numpy() == 0
    pre_mask = y_test.to_numpy() == 1

    normal_alert_rate = (
        predictions[normal_mask].mean()
        if normal_mask.any()
        else 0
    )

    pre_alert_rate = (
        predictions[pre_mask].mean()
        if pre_mask.any()
        else 0
    )

    pr_auc = average_precision_score(
        y_test,
        test_scores
    )

    roc_auc = roc_auc_score(
        y_test,
        test_scores
    )

    test = test.copy()
    test["risk_score"] = test_scores
    test["risk_alert"] = predictions

    warning_alerts = test[
        (test["target"] == 1)
        & (test["risk_alert"] == 1)
    ]

    if warning_alerts.empty:
        first_alert = None
        lead_minutes = None
    else:
        first_alert = warning_alerts[
            "window_start"
        ].min()

        lead_minutes = (
            failure_start - first_alert
        ).total_seconds() / 60

    print(
        "Normal alert rate:",
        round(normal_alert_rate * 100, 2),
        "%"
    )

    print(
        "Pre-failure alert rate:",
        round(pre_alert_rate * 100, 2),
        "%"
    )

    print("PR-AUC:", round(pr_auc, 4))
    print("ROC-AUC:", round(roc_auc, 4))

    if first_alert is None:
        print("Early warning: MISSED")
    else:
        print(
            "First warning:",
            first_alert,
            "| Lead time:",
            round(lead_minutes, 1),
            "minutes"
        )

    model_file = (
        f"{MODEL_DIR}/logistic_{fold_name}.joblib"
    )

    joblib.dump(
        {
            "pipeline": pipeline,
            "features": FEATURES,
            "threshold": threshold,
            "fold": fold_name,
            "failure_start": failure_start,
        },
        model_file,
    )

    results.append({
        "fold": fold_name,
        "training_positives": int(y_train.sum()),
        "training_negatives": int((y_train == 0).sum()),
        "test_normal_windows": int(normal_mask.sum()),
        "test_prefailure_windows": int(pre_mask.sum()),
        "threshold": threshold,
        "normal_alert_rate": normal_alert_rate,
        "prefailure_alert_rate": pre_alert_rate,
        "pr_auc": pr_auc,
        "roc_auc": roc_auc,
        "first_alert": first_alert,
        "lead_minutes": lead_minutes,
    })


results_df = pd.DataFrame(results)

results_df.to_csv(
    RESULT_FILE,
    index=False
)

print("\n====================")
print("WALK-FORWARD COMPLETE")
print("====================")
print(results_df)
print("\nResults saved:", RESULT_FILE)

import pandas as pd
import numpy as np
import joblib

INPUT_FILE = "data/features_v2/metropt_features_trend_30min.csv"
MODEL_FILE = "models/isolation_forest_trend_v1.joblib"
OUTPUT_FILE = "results/isolation_forest_trend_v1_scores.csv"

VALIDATION_START = pd.Timestamp("2020-04-01 00:00:00")
TEST_START = pd.Timestamp("2020-04-17 22:00:00")

FAILURE_STARTS = {
    "F1": pd.Timestamp("2020-04-18 00:00:00"),
    "F2": pd.Timestamp("2020-05-29 23:30:00"),
    "F3": pd.Timestamp("2020-06-05 10:00:00"),
    "F4": pd.Timestamp("2020-07-15 14:30:00"),
}

bundle = joblib.load(MODEL_FILE)
model = bundle["model"]
features = bundle["feature_columns"]

validation_parts = []

for chunk in pd.read_csv(
    INPUT_FILE,
    chunksize=50000,
    parse_dates=["window_start"],
):
    validation = chunk[
        (chunk["window_start"] >= VALIDATION_START)
        & (chunk["window_start"] < TEST_START)
        & (chunk["is_failure"] == 0)
        & (chunk["failure_within_2h"] == 0)
    ].copy()

    if not validation.empty:
        validation_parts.append(validation)

validation_df = pd.concat(validation_parts, ignore_index=True)

validation_scores = -model.decision_function(
    validation_df[features]
)

threshold = np.quantile(validation_scores, 0.95)

print("Validation windows:", len(validation_df))
print("5% calibrated threshold:", threshold)

first_write = True

normal_windows = normal_alerts = 0
pre_windows = pre_alerts = 0
failure_windows = failure_alerts = 0

first_alert = {name: None for name in FAILURE_STARTS}

normal_scores = []
pre_scores = []
failure_scores = []

for chunk in pd.read_csv(
    INPUT_FILE,
    chunksize=50000,
    parse_dates=["window_start"],
):
    chunk = chunk[
        chunk["window_start"] >= TEST_START
    ].copy()

    if chunk.empty:
        continue

    chunk["anomaly_score"] = -model.decision_function(
        chunk[features]
    )

    chunk["predicted_anomaly"] = (
        chunk["anomaly_score"] >= threshold
    ).astype(int)

    normal = (
        (chunk["is_failure"] == 0)
        & (chunk["failure_within_2h"] == 0)
    )

    pre = chunk["failure_within_2h"] == 1
    failure = chunk["is_failure"] == 1

    normal_windows += int(normal.sum())
    normal_alerts += int(
        chunk.loc[normal, "predicted_anomaly"].sum()
    )

    pre_windows += int(pre.sum())
    pre_alerts += int(
        chunk.loc[pre, "predicted_anomaly"].sum()
    )

    failure_windows += int(failure.sum())
    failure_alerts += int(
        chunk.loc[failure, "predicted_anomaly"].sum()
    )

    normal_scores.extend(
        chunk.loc[normal, "anomaly_score"].tolist()
    )

    pre_scores.extend(
        chunk.loc[pre, "anomaly_score"].tolist()
    )

    failure_scores.extend(
        chunk.loc[failure, "anomaly_score"].tolist()
    )

    for name, start in FAILURE_STARTS.items():
        warning_start = start - pd.Timedelta(hours=2)

        mask = (
            (chunk["window_start"] >= warning_start)
            & (chunk["window_start"] < start)
            & (chunk["predicted_anomaly"] == 1)
        )

        if mask.any():
            alert_time = chunk.loc[
                mask, "window_start"
            ].min()

            if (
                first_alert[name] is None
                or alert_time < first_alert[name]
            ):
                first_alert[name] = alert_time

    chunk[
        [
            "window_start",
            "anomaly_score",
            "predicted_anomaly",
            "is_failure",
            "failure_within_2h",
        ]
    ].to_csv(
        OUTPUT_FILE,
        mode="w" if first_write else "a",
        header=first_write,
        index=False,
    )

    first_write = False


print("\nALERT RATES")

print(
    "Normal:",
    round(normal_alerts / normal_windows * 100, 2),
    "%"
)

print(
    "Pre-failure:",
    round(pre_alerts / pre_windows * 100, 2),
    "%"
)

print(
    "Failure:",
    round(failure_alerts / failure_windows * 100, 2),
    "%"
)

print("\nEVENT WARNINGS")

for name, start in FAILURE_STARTS.items():
    alert = first_alert[name]

    if alert is None:
        print(name, "No warning")
    else:
        lead = (start - alert).total_seconds() / 60

        print(
            name,
            "Lead time:",
            round(lead, 1),
            "minutes"
        )


def score_summary(name, scores):
    s = pd.Series(scores)

    print("\n" + name)
    print("Median:", round(s.median(), 4))
    print("90th percentile:", round(s.quantile(0.90), 4))
    print("95th percentile:", round(s.quantile(0.95), 4))


print("\nSCORE DISTRIBUTIONS")

score_summary("NORMAL", normal_scores)
score_summary("PRE-FAILURE", pre_scores)
score_summary("FAILURE", failure_scores)

print("\nScores saved:", OUTPUT_FILE)

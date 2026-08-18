import pandas as pd
import numpy as np
import joblib

DATA_FILE = "data/features_v2/metropt_features_trend_30min.csv"

REGIME_MODEL_FILE = "models/regimes/kmeans_regime_v1.joblib"
REGIME_0_MODEL_FILE = "models/regime_anomaly/regime_0_iforest.joblib"
REGIME_1_MODEL_FILE = "models/regime_anomaly/regime_1_iforest.joblib"

OUTPUT_FILE = "results/regime_anomaly_scores.csv"

VALIDATION_START = pd.Timestamp("2020-04-01 00:00:00")
TEST_START = pd.Timestamp("2020-04-17 22:00:00")

FAILURE_STARTS = {
    "F1": pd.Timestamp("2020-04-18 00:00:00"),
    "F2": pd.Timestamp("2020-05-29 23:30:00"),
    "F3": pd.Timestamp("2020-06-05 10:00:00"),
    "F4": pd.Timestamp("2020-07-15 14:30:00"),
}

# Load operating-regime model
regime_bundle = joblib.load(REGIME_MODEL_FILE)

regime_model = regime_bundle["model"]
regime_scaler = regime_bundle["scaler"]
regime_features = regime_bundle["features"]

# Load regime-specific anomaly models
bundle_0 = joblib.load(REGIME_0_MODEL_FILE)
bundle_1 = joblib.load(REGIME_1_MODEL_FILE)

model_0 = bundle_0["model"]
model_1 = bundle_1["model"]

ml_features = bundle_0["feature_columns"]

# -------------------------------------------------
# STEP 1: CALIBRATE A SEPARATE THRESHOLD PER REGIME
# -------------------------------------------------

validation_scores = {
    0: [],
    1: [],
}

for chunk in pd.read_csv(
    DATA_FILE,
    chunksize=50000,
    parse_dates=["window_start"],
):

    validation = chunk[
        (chunk["window_start"] >= VALIDATION_START)
        & (chunk["window_start"] < TEST_START)
        & (chunk["is_failure"] == 0)
        & (chunk["failure_within_2h"] == 0)
    ].copy()

    if validation.empty:
        continue

    regime_input = regime_scaler.transform(
        validation[regime_features]
    )

    validation["regime"] = regime_model.predict(
        regime_input
    )

    for regime_number, model in [
        (0, model_0),
        (1, model_1),
    ]:

        subset = validation[
            validation["regime"] == regime_number
        ]

        if subset.empty:
            continue

        scores = -model.decision_function(
            subset[ml_features]
        )

        validation_scores[regime_number].extend(
            scores.tolist()
        )


thresholds = {}

for regime_number in [0, 1]:

    scores = np.array(
        validation_scores[regime_number]
    )

    threshold = np.quantile(
        scores,
        0.95
    )

    thresholds[regime_number] = threshold

    print(
        "Regime",
        regime_number,
        "validation windows:",
        len(scores)
    )

    print(
        "Regime",
        regime_number,
        "5% threshold:",
        threshold
    )


# -----------------------------------------
# STEP 2: TEST ON FUTURE UNSEEN DATA
# -----------------------------------------

first_write = True

normal_windows = 0
normal_alerts = 0

prefailure_windows = 0
prefailure_alerts = 0

failure_windows = 0
failure_alerts = 0

event_first_alert = {
    name: None
    for name in FAILURE_STARTS
}

regime_counts = {
    0: 0,
    1: 0,
}

for chunk in pd.read_csv(
    DATA_FILE,
    chunksize=50000,
    parse_dates=["window_start"],
):

    chunk = chunk[
        chunk["window_start"] >= TEST_START
    ].copy()

    if chunk.empty:
        continue

    regime_input = regime_scaler.transform(
        chunk[regime_features]
    )

    chunk["regime"] = regime_model.predict(
        regime_input
    )

    chunk["anomaly_score"] = np.nan
    chunk["predicted_anomaly"] = 0

    for regime_number, model in [
        (0, model_0),
        (1, model_1),
    ]:

        mask = (
            chunk["regime"] == regime_number
        )

        if not mask.any():
            continue

        regime_counts[regime_number] += int(
            mask.sum()
        )

        scores = -model.decision_function(
            chunk.loc[mask, ml_features]
        )

        chunk.loc[
            mask,
            "anomaly_score"
        ] = scores

        chunk.loc[
            mask,
            "predicted_anomaly"
        ] = (
            scores
            >= thresholds[regime_number]
        ).astype(int)

    normal = (
        (chunk["is_failure"] == 0)
        & (chunk["failure_within_2h"] == 0)
    )

    prefailure = (
        chunk["failure_within_2h"] == 1
    )

    failure = (
        chunk["is_failure"] == 1
    )

    normal_windows += int(normal.sum())

    normal_alerts += int(
        chunk.loc[
            normal,
            "predicted_anomaly"
        ].sum()
    )

    prefailure_windows += int(
        prefailure.sum()
    )

    prefailure_alerts += int(
        chunk.loc[
            prefailure,
            "predicted_anomaly"
        ].sum()
    )

    failure_windows += int(
        failure.sum()
    )

    failure_alerts += int(
        chunk.loc[
            failure,
            "predicted_anomaly"
        ].sum()
    )

    # Check early warning for each failure event
    for name, start in FAILURE_STARTS.items():

        warning_start = (
            start - pd.Timedelta(hours=2)
        )

        mask = (
            (chunk["window_start"] >= warning_start)
            & (chunk["window_start"] < start)
            & (chunk["predicted_anomaly"] == 1)
        )

        if mask.any():

            alert_time = chunk.loc[
                mask,
                "window_start"
            ].min()

            if (
                event_first_alert[name] is None
                or alert_time
                < event_first_alert[name]
            ):
                event_first_alert[name] = alert_time

    chunk[
        [
            "window_start",
            "regime",
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


print("\n====================")
print("REGIME USAGE")
print("====================")

print("Regime 0 windows:", regime_counts[0])
print("Regime 1 windows:", regime_counts[1])


print("\n====================")
print("ALERT RATES")
print("====================")

print(
    "Normal:",
    round(
        normal_alerts
        / normal_windows
        * 100,
        2,
    ),
    "%"
)

print(
    "Pre-failure:",
    round(
        prefailure_alerts
        / prefailure_windows
        * 100,
        2,
    ),
    "%"
)

print(
    "Failure:",
    round(
        failure_alerts
        / failure_windows
        * 100,
        2,
    ),
    "%"
)


print("\n====================")
print("EVENT WARNINGS")
print("====================")

for name, start in FAILURE_STARTS.items():

    alert = event_first_alert[name]

    if alert is None:

        print(
            name,
            "No warning"
        )

    else:

        lead = (
            start - alert
        ).total_seconds() / 60

        print(
            name,
            "First alert:",
            alert,
            "| Lead time:",
            round(lead, 1),
            "minutes"
        )


print("\nScores saved:", OUTPUT_FILE)

import pandas as pd
import joblib

INPUT_FILE = "data/features/metropt_features_1min.csv"
MODEL_FILE = "models/isolation_forest_v1.joblib"
OUTPUT_FILE = "results/isolation_forest_v1_scores.csv"

TEST_START = pd.Timestamp("2020-04-17 22:00:00")

FAILURE_STARTS = {
    "F1": pd.Timestamp("2020-04-18 00:00:00"),
    "F2": pd.Timestamp("2020-05-29 23:30:00"),
    "F3": pd.Timestamp("2020-06-05 10:00:00"),
    "F4": pd.Timestamp("2020-07-15 14:30:00"),
}

bundle = joblib.load(MODEL_FILE)
model = bundle["model"]
feature_columns = bundle["feature_columns"]

first_write = True

total_windows = 0
normal_windows = 0
normal_alerts = 0
prefailure_windows = 0
prefailure_alerts = 0
failure_windows = 0
failure_alerts = 0

event_first_alert = {name: None for name in FAILURE_STARTS}

for chunk in pd.read_csv(
    INPUT_FILE,
    chunksize=50000,
    parse_dates=["window_start"],
):
    chunk = chunk[chunk["window_start"] >= TEST_START].copy()

    if chunk.empty:
        continue

    X = chunk[feature_columns]

    # Isolation Forest:
    # lower decision_function = more abnormal
    # we invert it so higher anomaly_score = more abnormal
    chunk["anomaly_score"] = -model.decision_function(X)

    chunk["predicted_anomaly"] = (
        model.predict(X) == -1
    ).astype(int)

    normal_mask = (
        (chunk["is_failure"] == 0)
        & (chunk["failure_within_2h"] == 0)
    )

    prefailure_mask = chunk["failure_within_2h"] == 1
    failure_mask = chunk["is_failure"] == 1

    total_windows += len(chunk)

    normal_windows += int(normal_mask.sum())
    normal_alerts += int(
        chunk.loc[normal_mask, "predicted_anomaly"].sum()
    )

    prefailure_windows += int(prefailure_mask.sum())
    prefailure_alerts += int(
        chunk.loc[prefailure_mask, "predicted_anomaly"].sum()
    )

    failure_windows += int(failure_mask.sum())
    failure_alerts += int(
        chunk.loc[failure_mask, "predicted_anomaly"].sum()
    )

    for name, start in FAILURE_STARTS.items():
        pre_start = start - pd.Timedelta(hours=2)

        event_mask = (
            (chunk["window_start"] >= pre_start)
            & (chunk["window_start"] < start)
            & (chunk["predicted_anomaly"] == 1)
        )

        if event_mask.any():
            first_alert = chunk.loc[
                event_mask, "window_start"
            ].min()

            if (
                event_first_alert[name] is None
                or first_alert < event_first_alert[name]
            ):
                event_first_alert[name] = first_alert

    output_columns = [
        "window_start",
        "anomaly_score",
        "predicted_anomaly",
        "is_failure",
        "failure_within_2h",
    ]

    chunk[output_columns].to_csv(
        OUTPUT_FILE,
        mode="w" if first_write else "a",
        header=first_write,
        index=False,
    )

    first_write = False


print("Test windows:", total_windows)

print("\nNORMAL PERIODS")
print("Normal windows:", normal_windows)
print("Normal anomaly alerts:", normal_alerts)

print("\n2-HOUR PRE-FAILURE PERIODS")
print("Pre-failure windows:", prefailure_windows)
print("Pre-failure anomaly alerts:", prefailure_alerts)

print("\nFAILURE PERIODS")
print("Failure windows:", failure_windows)
print("Failure anomaly alerts:", failure_alerts)

print("\nEVENT EARLY-WARNING RESULTS")

for name, start in FAILURE_STARTS.items():
    first_alert = event_first_alert[name]

    if first_alert is None:
        print(name, "No anomaly detected in 2-hour warning window")
    else:
        lead_minutes = (
            start - first_alert
        ).total_seconds() / 60

        print(
            name,
            "First alert:",
            first_alert,
            "| Lead time:",
            round(lead_minutes, 1),
            "minutes",
        )

print("\nScores saved:", OUTPUT_FILE)

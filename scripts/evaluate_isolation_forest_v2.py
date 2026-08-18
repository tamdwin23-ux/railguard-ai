import pandas as pd
import joblib

INPUT_FILE = "data/features/metropt_features_1min.csv"
MODEL_FILE = "models/isolation_forest_v2.joblib"
OUTPUT_FILE = "results/isolation_forest_v2_scores.csv"

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
threshold = bundle["threshold"]

normal_windows = normal_alerts = 0
pre_windows = pre_alerts = 0
failure_windows = failure_alerts = 0

first_alert = {name: None for name in FAILURE_STARTS}
first_write = True

for chunk in pd.read_csv(
    INPUT_FILE,
    chunksize=50000,
    parse_dates=["window_start"]
):
    chunk = chunk[chunk["window_start"] >= TEST_START].copy()

    if chunk.empty:
        continue

    X = chunk[features]

    chunk["anomaly_score"] = -model.decision_function(X)

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

    for name, start in FAILURE_STARTS.items():
        warning_start = start - pd.Timedelta(hours=2)

        mask = (
            (chunk["window_start"] >= warning_start)
            & (chunk["window_start"] < start)
            & (chunk["predicted_anomaly"] == 1)
        )

        if mask.any():
            alert_time = chunk.loc[mask, "window_start"].min()

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


print("NORMAL")
print("Windows:", normal_windows)
print("Alerts:", normal_alerts)
print(
    "Alert rate:",
    round(normal_alerts / normal_windows * 100, 2),
    "%"
)

print("\nPRE-FAILURE")
print("Windows:", pre_windows)
print("Alerts:", pre_alerts)
print(
    "Alert rate:",
    round(pre_alerts / pre_windows * 100, 2),
    "%"
)

print("\nFAILURE")
print("Windows:", failure_windows)
print("Alerts:", failure_alerts)
print(
    "Alert rate:",
    round(failure_alerts / failure_windows * 100, 2),
    "%"
)

print("\nEVENT EARLY-WARNING RESULTS")

for name, start in FAILURE_STARTS.items():
    alert = first_alert[name]

    if alert is None:
        print(name, "No alert in 2-hour warning window")
    else:
        lead = (start - alert).total_seconds() / 60

        print(
            name,
            "First alert:",
            alert,
            "| Lead time:",
            round(lead, 1),
            "minutes"
        )

print("\nThreshold:", threshold)
print("Scores saved:", OUTPUT_FILE)

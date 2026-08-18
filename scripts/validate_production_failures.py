import pandas as pd

from app.model_service import score_feature_window, required_features
from app.risk_engine import RuntimeRiskEngine


FAILURES = {
    "F1": (
        pd.Timestamp("2020-04-18 00:00:00"),
        pd.Timestamp("2020-04-18 23:59:59"),
    ),
    "F2": (
        pd.Timestamp("2020-05-29 23:30:00"),
        pd.Timestamp("2020-05-30 06:00:00"),
    ),
    "F3": (
        pd.Timestamp("2020-06-05 10:00:00"),
        pd.Timestamp("2020-06-07 14:30:00"),
    ),
    "F4": (
        pd.Timestamp("2020-07-15 14:30:00"),
        pd.Timestamp("2020-07-15 19:00:00"),
    ),
}

FEATURES = required_features()


for failure_id, (failure_start, failure_end) in FAILURES.items():

    engine = RuntimeRiskEngine()

    replay_start = failure_start - pd.Timedelta(minutes=60)
    replay_end = min(
        failure_end,
        failure_start + pd.Timedelta(minutes=120),
    )

    confirmed = None

    for chunk in pd.read_csv(
        "data/features_v2/metropt_features_trend_30min.csv",
        chunksize=10000,
        parse_dates=["window_start"],
    ):
        rows = chunk[
            (chunk["window_start"] >= replay_start) &
            (chunk["window_start"] <= replay_end)
        ]

        if rows.empty:
            continue

        for _, row in rows.iterrows():

            feature_data = {
                feature: float(row[feature])
                for feature in FEATURES
            }

            prediction = score_feature_window(
                feature_data
            )

            runtime = engine.process(
                row["window_start"],
                prediction,
            )

            event = runtime["event"]

            if (
                event
                and event["event_type"] == "CONFIRMED_FAULT"
            ):
                confirmed = pd.Timestamp(
                    event["confirmed_at"]
                )
                break

        if confirmed is not None:
            break

    if confirmed is None:
        print(
            failure_id,
            "MISSED",
        )
        continue

    delta_minutes = (
        confirmed - failure_start
    ).total_seconds() / 60

    print(
        failure_id,
        "failure_start=",
        failure_start,
        "confirmed_at=",
        confirmed,
        "delta_minutes=",
        round(delta_minutes, 1),
    )

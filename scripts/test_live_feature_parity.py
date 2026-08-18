import pandas as pd

from app.feature_engine import LiveFeatureEngine
from app.model_service import required_features


START = pd.Timestamp("2020-06-05 09:30:00")
END = pd.Timestamp("2020-06-05 10:02:00")
TARGET = pd.Timestamp("2020-06-05 10:00:00")

SENSORS = [
    "TP2",
    "TP3",
    "H1",
    "DV_pressure",
    "Reservoirs",
    "Oil_temperature",
    "Motor_current",
    "COMP",
    "DV_eletric",
    "Towers",
    "MPG",
    "LPS",
    "Pressure_switch",
    "Oil_level",
    "Caudal_impulses",
]

engine = LiveFeatureEngine()
live_window = None

for chunk in pd.read_csv(
    "data/processed/metropt_clean.csv",
    chunksize=50000,
    parse_dates=["timestamp"],
):
    chunk = chunk[
        (chunk["timestamp"] >= START) &
        (chunk["timestamp"] < END)
    ]

    if chunk.empty:
        continue

    for _, row in chunk.iterrows():
        sensors = {
            name: float(row[name])
            for name in SENSORS
        }

        result = engine.add_reading(
            row["timestamp"],
            sensors,
        )

        completed = result["completed_window"]

        if (
            completed is not None
            and pd.Timestamp(
                completed["window_start"]
            ) == TARGET
        ):
            live_window = completed
            break

    if live_window is not None:
        break


expected = None

for chunk in pd.read_csv(
    "data/features_v2/metropt_features_trend_30min.csv",
    chunksize=10000,
    parse_dates=["window_start"],
):
    match = chunk[
        chunk["window_start"] == TARGET
    ]

    if not match.empty:
        expected = match.iloc[0]
        break


if live_window is None:
    raise SystemExit("LIVE TARGET WINDOW NOT CREATED")

if expected is None:
    raise SystemExit("EXPECTED TARGET WINDOW NOT FOUND")


differences = []

for feature in required_features():
    live = float(
        live_window["features"][feature]
    )
    trained = float(expected[feature])
    diff = abs(live - trained)

    differences.append(
        (feature, live, trained, diff)
    )


differences.sort(
    key=lambda x: x[3],
    reverse=True,
)

print("TOP DIFFERENCES")

for feature, live, trained, diff in differences[:15]:
    print(
        feature,
        "live=",
        round(live, 8),
        "trained=",
        round(trained, 8),
        "diff=",
        round(diff, 8),
    )

print()
print(
    "MAX_DIFF:",
    differences[0][3],
)

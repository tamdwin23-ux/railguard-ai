import pandas as pd

INPUT_FILE = "data/features/metropt_features_1min.csv"
OUTPUT_FILE = "data/features_v2/metropt_features_trend_30min.csv"

SENSORS = [
    "TP2",
    "TP3",
    "H1",
    "DV_pressure",
    "Reservoirs",
    "Oil_temperature",
    "Motor_current",
]

SENSOR_MEANS = [f"{sensor}_mean" for sensor in SENSORS]

carry = pd.DataFrame()
first_write = True

for chunk in pd.read_csv(
    INPUT_FILE,
    chunksize=50000,
    parse_dates=["window_start"],
):
    chunk = chunk.sort_values("window_start")
    chunk_start = chunk["window_start"].min()

    if not carry.empty:
        data = pd.concat([carry, chunk], ignore_index=True)
    else:
        data = chunk.copy()

    data = data.sort_values("window_start")

    indexed = data.set_index("window_start")

    for column in SENSOR_MEANS:
        rolling = indexed[column].rolling(
            "30min",
            min_periods=1
        )

        indexed[f"{column}_30m_mean"] = rolling.mean()

        indexed[f"{column}_30m_std"] = (
            rolling.std().fillna(0)
        )

        indexed[f"{column}_vs_30m_mean"] = (
            indexed[column]
            - indexed[f"{column}_30m_mean"]
        )

    features = indexed.reset_index()

    output = features[
        features["window_start"] >= chunk_start
    ].copy()

    output.to_csv(
        OUTPUT_FILE,
        mode="w" if first_write else "a",
        header=first_write,
        index=False,
    )

    first_write = False

    last_time = data["window_start"].max()

    carry = data[
        data["window_start"]
        >= last_time - pd.Timedelta(minutes=30)
    ].copy()

print("30-minute trend features complete.")

import pandas as pd

INPUT_FILE = "data/processed/metropt_clean.csv"
OUTPUT_FILE = "data/features/metropt_features_1min.csv"

CONTINUOUS = [
    "TP2",
    "TP3",
    "H1",
    "DV_pressure",
    "Reservoirs",
    "Oil_temperature",
    "Motor_current",
]

BINARY = [
    "COMP",
    "DV_eletric",
    "Towers",
    "MPG",
    "LPS",
    "Pressure_switch",
    "Oil_level",
    "Caudal_impulses",
]

carry = pd.DataFrame()
first_write = True


def create_features(data):
    data = data.copy()

    data["window_start"] = data["timestamp"].dt.floor("min")

    continuous_features = (
        data.groupby("window_start")[CONTINUOUS]
        .agg(["mean", "std", "min", "max"])
    )

    continuous_features.columns = [
        f"{sensor}_{stat}"
        for sensor, stat in continuous_features.columns
    ]

    binary_features = (
        data.groupby("window_start")[BINARY]
        .mean()
        .add_suffix("_active_ratio")
    )

    labels = data.groupby("window_start")[
        ["is_failure", "failure_within_2h"]
    ].max()

    row_count = (
        data.groupby("window_start")
        .size()
        .rename("readings_in_window")
    )

    features = pd.concat(
        [
            continuous_features,
            binary_features,
            labels,
            row_count,
        ],
        axis=1,
    )

    features = features.reset_index()

    std_columns = [
        column for column in features.columns
        if column.endswith("_std")
    ]

    features[std_columns] = features[std_columns].fillna(0)

    return features


for chunk in pd.read_csv(
    INPUT_FILE,
    chunksize=100000,
    parse_dates=["timestamp"],
):
    if not carry.empty:
        chunk = pd.concat([carry, chunk], ignore_index=True)

    chunk["window_start"] = chunk["timestamp"].dt.floor("min")

    last_window = chunk["window_start"].max()

    complete = chunk[chunk["window_start"] < last_window].copy()
    carry = chunk[chunk["window_start"] == last_window].copy()

    if not complete.empty:
        features = create_features(complete)

        features.to_csv(
            OUTPUT_FILE,
            mode="w" if first_write else "a",
            header=first_write,
            index=False,
        )

        first_write = False


if not carry.empty:
    features = create_features(carry)

    features.to_csv(
        OUTPUT_FILE,
        mode="w" if first_write else "a",
        header=first_write,
        index=False,
    )


print("1-minute feature engineering complete.")

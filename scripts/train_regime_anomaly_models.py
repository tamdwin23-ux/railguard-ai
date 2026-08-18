import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

DATA_FILE = "data/features_v2/metropt_features_trend_30min.csv"

REGIME_MODEL_FILE = "models/regimes/kmeans_regime_v1.joblib"

OUTPUT_MODEL_0 = "models/regime_anomaly/regime_0_iforest.joblib"
OUTPUT_MODEL_1 = "models/regime_anomaly/regime_1_iforest.joblib"

TRAIN_END = pd.Timestamp("2020-04-01 00:00:00")

EXCLUDE_COLUMNS = [
    "window_start",
    "is_failure",
    "failure_within_2h",
    "readings_in_window",
]

# Load the operating-regime model
regime_bundle = joblib.load(REGIME_MODEL_FILE)

regime_model = regime_bundle["model"]
regime_scaler = regime_bundle["scaler"]
regime_features = regime_bundle["features"]

regime_0_parts = []
regime_1_parts = []

# Read safely in chunks
for chunk in pd.read_csv(
    DATA_FILE,
    chunksize=50000,
    parse_dates=["window_start"],
):

    # Train only on historical normal operation
    normal = chunk[
        (chunk["window_start"] < TRAIN_END)
        & (chunk["is_failure"] == 0)
        & (chunk["failure_within_2h"] == 0)
    ].copy()

    if normal.empty:
        continue

    # Determine operating regime
    regime_input = regime_scaler.transform(
        normal[regime_features]
    )

    normal["regime"] = regime_model.predict(
        regime_input
    )

    regime_0 = normal[
        normal["regime"] == 0
    ].copy()

    regime_1 = normal[
        normal["regime"] == 1
    ].copy()

    if not regime_0.empty:
        regime_0_parts.append(regime_0)

    if not regime_1.empty:
        regime_1_parts.append(regime_1)


regime_0_df = pd.concat(
    regime_0_parts,
    ignore_index=True
)

regime_1_df = pd.concat(
    regime_1_parts,
    ignore_index=True
)

feature_columns = [
    column
    for column in regime_0_df.columns
    if column not in EXCLUDE_COLUMNS
    and column != "regime"
]

print("ML features:", len(feature_columns))
print("Regime 0 training windows:", len(regime_0_df))
print("Regime 1 training windows:", len(regime_1_df))


def train_model(data, regime_number, output_file):

    X = data[feature_columns]

    print(
        "\nTraining anomaly model for Regime",
        regime_number
    )

    model = IsolationForest(
        n_estimators=200,
        max_samples=2048,
        contamination="auto",
        random_state=42,
        n_jobs=1,
    )

    model.fit(X)

    bundle = {
        "model": model,
        "feature_columns": feature_columns,
        "regime": regime_number,
        "training_windows": len(data),
        "train_start": data["window_start"].min(),
        "train_end": data["window_start"].max(),
    }

    joblib.dump(
        bundle,
        output_file
    )

    print("Saved:", output_file)


train_model(
    regime_0_df,
    0,
    OUTPUT_MODEL_0
)

train_model(
    regime_1_df,
    1,
    OUTPUT_MODEL_1
)

print("\nRegime-specific anomaly training complete.")

import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest

INPUT_FILE = "data/features/metropt_features_1min.csv"
MODEL_FILE = "models/isolation_forest_v2.joblib"

TRAIN_END = pd.Timestamp("2020-04-01 00:00:00")
VALIDATION_END = pd.Timestamp("2020-04-17 22:00:00")

TARGET_VALIDATION_ALERT_RATE = 0.01

EXCLUDE_COLUMNS = [
    "window_start",
    "is_failure",
    "failure_within_2h",
    "readings_in_window",
]

train_parts = []
validation_parts = []

for chunk in pd.read_csv(
    INPUT_FILE,
    chunksize=50000,
    parse_dates=["window_start"],
):
    train_chunk = chunk[
        (chunk["window_start"] < TRAIN_END)
        & (chunk["is_failure"] == 0)
        & (chunk["failure_within_2h"] == 0)
    ].copy()

    validation_chunk = chunk[
        (chunk["window_start"] >= TRAIN_END)
        & (chunk["window_start"] < VALIDATION_END)
        & (chunk["is_failure"] == 0)
        & (chunk["failure_within_2h"] == 0)
    ].copy()

    if not train_chunk.empty:
        train_parts.append(train_chunk)

    if not validation_chunk.empty:
        validation_parts.append(validation_chunk)

train_df = pd.concat(train_parts, ignore_index=True)
validation_df = pd.concat(validation_parts, ignore_index=True)

feature_columns = [
    col for col in train_df.columns
    if col not in EXCLUDE_COLUMNS
]

X_train = train_df[feature_columns]
X_validation = validation_df[feature_columns]

print("Training windows:", len(X_train))
print("Validation windows:", len(X_validation))
print("ML features:", len(feature_columns))

model = IsolationForest(
    n_estimators=200,
    max_samples=2048,
    contamination="auto",
    random_state=42,
    n_jobs=1,
)

print("\nTraining V2 Isolation Forest...")
model.fit(X_train)

validation_scores = -model.decision_function(X_validation)

threshold = np.quantile(
    validation_scores,
    1 - TARGET_VALIDATION_ALERT_RATE
)

validation_alert_rate = (
    validation_scores >= threshold
).mean()

print("Calibrated anomaly threshold:", threshold)
print(
    "Validation alert rate:",
    round(validation_alert_rate * 100, 2),
    "%"
)

bundle = {
    "model": model,
    "feature_columns": feature_columns,
    "threshold": threshold,
    "target_validation_alert_rate": TARGET_VALIDATION_ALERT_RATE,
    "train_start": train_df["window_start"].min(),
    "train_end": train_df["window_start"].max(),
    "validation_start": validation_df["window_start"].min(),
    "validation_end": validation_df["window_start"].max(),
}

joblib.dump(bundle, MODEL_FILE)

print("Model saved:", MODEL_FILE)

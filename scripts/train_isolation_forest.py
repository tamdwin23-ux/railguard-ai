import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

INPUT_FILE = "data/features/metropt_features_1min.csv"
MODEL_FILE = "models/isolation_forest_v1.joblib"

TRAIN_END = pd.Timestamp("2020-04-17 22:00:00")

EXCLUDE_COLUMNS = [
    "window_start",
    "is_failure",
    "failure_within_2h",
    "readings_in_window",
]

train_parts = []

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

    if not train_chunk.empty:
        train_parts.append(train_chunk)

train_df = pd.concat(train_parts, ignore_index=True)

feature_columns = [
    col for col in train_df.columns
    if col not in EXCLUDE_COLUMNS
]

X_train = train_df[feature_columns]

print("Training windows:", len(X_train))
print("ML features:", len(feature_columns))
print("Training start:", train_df["window_start"].min())
print("Training end:", train_df["window_start"].max())

model = IsolationForest(
    n_estimators=200,
    max_samples=2048,
    contamination="auto",
    random_state=42,
    n_jobs=1,
)

print("\nTraining Isolation Forest...")
model.fit(X_train)

model_bundle = {
    "model": model,
    "feature_columns": feature_columns,
    "train_start": train_df["window_start"].min(),
    "train_end": train_df["window_start"].max(),
}

joblib.dump(model_bundle, MODEL_FILE)

print("Model saved:", MODEL_FILE)

import json
import numpy as np
import pandas as pd

from app.model_service import required_features

FEATURES = required_features()

count = 0
total = np.zeros(len(FEATURES))
total_sq = np.zeros(len(FEATURES))

for chunk in pd.read_csv(
    "data/features_v2/metropt_features_trend_30min.csv",
    chunksize=20000,
    parse_dates=["window_start"],
):
    chunk = chunk[
        (chunk["window_start"] < "2020-04-01 00:00:00") &
        (chunk["is_failure"] == 0)
    ]

    if chunk.empty:
        continue

    values = chunk[FEATURES].to_numpy(dtype=float)

    count += len(values)
    total += values.sum(axis=0)
    total_sq += (values ** 2).sum(axis=0)

means = total / count

variance = (
    total_sq / count
    - means ** 2
)

variance = np.maximum(
    variance,
    1e-12,
)

stds = np.sqrt(variance)

baseline = {
    "training_windows": int(count),
    "features": {
        feature: {
            "mean": float(mean),
            "std": float(std),
        }
        for feature, mean, std in zip(
            FEATURES,
            means,
            stds,
        )
    },
}

with open(
    "models/feature_baseline.json",
    "w",
) as file:
    json.dump(
        baseline,
        file,
        indent=2,
    )

print(
    "BASELINE WINDOWS:",
    count,
)
print(
    "FEATURES:",
    len(FEATURES),
)
print(
    "SAVED: models/feature_baseline.json"
)

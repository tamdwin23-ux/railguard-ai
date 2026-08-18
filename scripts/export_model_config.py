import json
import pandas as pd
import numpy as np
import joblib

DATA_FILE = "data/features_v2/metropt_features_trend_30min.csv"

GLOBAL_MODEL_FILE = "models/isolation_forest_trend_v1.joblib"
REGIME_MODEL_FILE = "models/regimes/kmeans_regime_v1.joblib"
REGIME_0_MODEL_FILE = "models/regime_anomaly/regime_0_iforest.joblib"
REGIME_1_MODEL_FILE = "models/regime_anomaly/regime_1_iforest.joblib"

OUTPUT_FILE = "models/railguard_model_config.json"

VALIDATION_START = pd.Timestamp("2020-04-01 00:00:00")
TEST_START = pd.Timestamp("2020-04-17 22:00:00")

global_bundle = joblib.load(GLOBAL_MODEL_FILE)
regime_bundle = joblib.load(REGIME_MODEL_FILE)
regime_0_bundle = joblib.load(REGIME_0_MODEL_FILE)
regime_1_bundle = joblib.load(REGIME_1_MODEL_FILE)

global_model = global_bundle["model"]
global_features = global_bundle["feature_columns"]

regime_model = regime_bundle["model"]
regime_scaler = regime_bundle["scaler"]
regime_features = regime_bundle["features"]

regime_models = {
    0: regime_0_bundle["model"],
    1: regime_1_bundle["model"],
}

regime_anomaly_features = (
    regime_0_bundle["feature_columns"]
)

global_scores = []

regime_scores = {
    0: [],
    1: [],
}

for chunk in pd.read_csv(
    DATA_FILE,
    chunksize=50000,
    parse_dates=["window_start"],
):

    validation = chunk[
        (chunk["window_start"] >= VALIDATION_START)
        & (chunk["window_start"] < TEST_START)
        & (chunk["is_failure"] == 0)
        & (chunk["failure_within_2h"] == 0)
    ].copy()

    if validation.empty:
        continue

    scores = -global_model.decision_function(
        validation[global_features]
    )

    global_scores.extend(scores.tolist())

    regime_input = regime_scaler.transform(
        validation[regime_features]
    )

    validation["regime"] = regime_model.predict(
        regime_input
    )

    for regime_number in [0, 1]:

        subset = validation[
            validation["regime"] == regime_number
        ]

        if subset.empty:
            continue

        scores = -regime_models[
            regime_number
        ].decision_function(
            subset[regime_anomaly_features]
        )

        regime_scores[
            regime_number
        ].extend(scores.tolist())


global_threshold = float(
    np.quantile(
        np.array(global_scores),
        0.95
    )
)

regime_0_threshold = float(
    np.quantile(
        np.array(regime_scores[0]),
        0.95
    )
)

regime_1_threshold = float(
    np.quantile(
        np.array(regime_scores[1]),
        0.95
    )
)

config = {
    "version": "railguard-v1",
    "global_model": {
        "path": GLOBAL_MODEL_FILE,
        "threshold": global_threshold,
    },
    "regime_model": {
        "path": REGIME_MODEL_FILE,
        "regimes": 2,
    },
    "regime_anomaly_models": {
        "0": {
            "path": REGIME_0_MODEL_FILE,
            "threshold": regime_0_threshold,
        },
        "1": {
            "path": REGIME_1_MODEL_FILE,
            "threshold": regime_1_threshold,
        },
    },
    "risk_engine": {
        "fault_anomaly_minutes": 20,
        "gap_tolerance_minutes": 2,
        "watch_minimum_minutes": 3,
        "incident_merge_minutes": 240,
    },
    "validation_period": {
        "start": str(VALIDATION_START),
        "end": str(TEST_START),
    },
}

with open(
    OUTPUT_FILE,
    "w"
) as file:
    json.dump(
        config,
        file,
        indent=2
    )

print("Global threshold:", global_threshold)
print("Regime 0 threshold:", regime_0_threshold)
print("Regime 1 threshold:", regime_1_threshold)

print("\nSaved:", OUTPUT_FILE)

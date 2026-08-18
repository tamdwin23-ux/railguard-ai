from pathlib import Path
import json

import joblib
import pandas as pd
from app.explainer import explain_features


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "models" / "railguard_model_config.json"


with open(CONFIG_FILE, "r") as file:
    CONFIG = json.load(file)


def resolve_model_path(relative_path):
    return BASE_DIR / relative_path


# Load global anomaly model
global_bundle = joblib.load(
    resolve_model_path(
        CONFIG["global_model"]["path"]
    )
)

global_model = global_bundle["model"]
global_features = global_bundle["feature_columns"]
global_threshold = CONFIG["global_model"]["threshold"]


# Load operating-regime model
regime_bundle = joblib.load(
    resolve_model_path(
        CONFIG["regime_model"]["path"]
    )
)

regime_model = regime_bundle["model"]
regime_scaler = regime_bundle["scaler"]
regime_features = regime_bundle["features"]


# Load regime-specific anomaly models
regime_models = {}
regime_thresholds = {}
regime_anomaly_features = None

for regime_id in ["0", "1"]:

    model_config = CONFIG[
        "regime_anomaly_models"
    ][regime_id]

    bundle = joblib.load(
        resolve_model_path(
            model_config["path"]
        )
    )

    regime_models[int(regime_id)] = bundle["model"]

    regime_thresholds[int(regime_id)] = (
        model_config["threshold"]
    )

    if regime_anomaly_features is None:
        regime_anomaly_features = bundle[
            "feature_columns"
        ]


def required_features():
    features = set()

    features.update(global_features)
    features.update(regime_features)
    features.update(regime_anomaly_features)

    return sorted(features)


def score_feature_window(feature_data):

    missing = [
        feature
        for feature in required_features()
        if feature not in feature_data
    ]

    if missing:
        raise ValueError(
            f"Missing required features: {missing}"
        )

    row = pd.DataFrame(
        [feature_data]
    )

    # Global anomaly score
    global_score = float(
        -global_model.decision_function(
            row[global_features]
        )[0]
    )

    global_anomaly = (
        global_score >= global_threshold
    )

    # Determine operating regime
    scaled_regime_input = (
        regime_scaler.transform(
            row[regime_features]
        )
    )

    regime = int(
        regime_model.predict(
            scaled_regime_input
        )[0]
    )

    # Regime-specific anomaly score
    regime_score = float(
        -regime_models[
            regime
        ].decision_function(
            row[regime_anomaly_features]
        )[0]
    )

    regime_threshold = regime_thresholds[
        regime
    ]

    regime_anomaly = (
        regime_score >= regime_threshold
    )

    # Minute-level decision state
    if not global_anomaly and not regime_anomaly:
        risk_state = "LOW"

    elif not global_anomaly and regime_anomaly:
        risk_state = "WATCH"

    elif global_anomaly and not regime_anomaly:
        risk_state = "HIGH"

    else:
        risk_state = "DUAL"

    return {
        "regime": regime,
        "global_anomaly_score": global_score,
        "global_threshold": global_threshold,
        "global_anomaly": bool(global_anomaly),
        "regime_anomaly_score": regime_score,
        "regime_threshold": regime_threshold,
        "regime_anomaly": bool(regime_anomaly),
        "risk_state": risk_state,
        "explanation": explain_features(feature_data),
    }

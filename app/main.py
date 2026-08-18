from pathlib import Path
import json

from fastapi import FastAPI

BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_FILE = BASE_DIR / "models" / "railguard_model_config.json"

with open(CONFIG_FILE, "r") as file:
    MODEL_CONFIG = json.load(file)

app = FastAPI(
    title="RailGuard AI API",
    description="Railway compressor predictive maintenance and failure intelligence API",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "service": "RailGuard AI",
        "status": "running",
        "version": MODEL_CONFIG["version"],
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "railguard-api",
    }


@app.get("/model-info")
def model_info():
    return {
        "version": MODEL_CONFIG["version"],
        "global_threshold": MODEL_CONFIG["global_model"]["threshold"],
        "regimes": MODEL_CONFIG["regime_model"]["regimes"],
        "fault_anomaly_minutes": MODEL_CONFIG["risk_engine"][
            "fault_anomaly_minutes"
        ],
        "gap_tolerance_minutes": MODEL_CONFIG["risk_engine"][
            "gap_tolerance_minutes"
        ],
    }
from fastapi import HTTPException
from pydantic import BaseModel

from app.model_service import (
    score_feature_window,
    required_features,
)


class PredictionRequest(BaseModel):
    features: dict[str, float]


@app.get("/required-features")
def get_required_features():
    return {
        "count": len(required_features()),
        "features": required_features(),
    }


@app.post("/predict")
def predict(request: PredictionRequest):
    try:
        result = score_feature_window(
            request.features
        )

        return {
            "service": "RailGuard AI",
            "model_version": MODEL_CONFIG["version"],
            "prediction": result,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

from app.risk_engine import risk_engine
from app.s3_service import save_prediction, save_sensor_reading, save_drift_event
from app.feature_engine import feature_engine
from app.drift_monitor import drift_monitor
from app.n8n_service import send_maintenance_event


class RuntimePredictionRequest(BaseModel):
    timestamp: str
    features: dict[str, float]


@app.post("/predict-risk")
def predict_risk(request: RuntimePredictionRequest):
    try:
        prediction = score_feature_window(request.features)

        runtime = risk_engine.process(
            request.timestamp,
            prediction,
        )

        response = {
            "service": "RailGuard AI",
            "model_version": MODEL_CONFIG["version"],
            "timestamp": request.timestamp,
            "prediction": prediction,
            "runtime": runtime,
        }

        response["s3"] = save_prediction(
            request.timestamp,
            response,
        )

        return response

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@app.post("/resolve-fault")
def resolve_fault():
    result = risk_engine.resolve_fault()

    return {
        "service": "RailGuard AI",
        "result": result,
    }


class SensorReadingRequest(BaseModel):
    timestamp: str
    TP2: float
    TP3: float
    H1: float
    DV_pressure: float
    Reservoirs: float
    Oil_temperature: float
    Motor_current: float
    COMP: float
    DV_eletric: float
    Towers: float
    MPG: float
    LPS: float
    Pressure_switch: float
    Oil_level: float
    Caudal_impulses: float


@app.post("/ingest")
def ingest_sensor_reading(request: SensorReadingRequest):
    sensor_data = request.model_dump()
    timestamp = sensor_data.pop("timestamp")

    raw_s3 = save_sensor_reading(
        timestamp,
        sensor_data,
    )

    feature_result = feature_engine.add_reading(
        timestamp,
        sensor_data,
    )

    response = {
        "service": "RailGuard AI",
        "status": feature_result["status"],
        "timestamp": timestamp,
        "sensor_count": len(sensor_data),
        "raw_s3": raw_s3,
    }

    completed = feature_result["completed_window"]

    if completed is not None:
        response["window"] = {
            "window_start": completed["window_start"],
            "reading_count": completed["reading_count"],
            "history_windows": completed["history_windows"],
            "ready_for_prediction": completed["ready_for_prediction"],
        }

        if not completed["ready_for_prediction"]:
            response["status"] = "ml_warming_up"
            return response

        prediction = score_feature_window(
            completed["features"]
        )

        runtime = risk_engine.process(
            completed["window_start"],
            prediction,
        )

        maintenance_automation = None

        if runtime["event"] is not None:
            if runtime["event"]["event_type"] == "CONFIRMED_FAULT":
                try:
                    maintenance_automation = send_maintenance_event(
                        runtime["event"]
                    )
                except Exception as error:
                    maintenance_automation = {
                        "sent": False,
                        "error": str(error),
                    }

        drift = drift_monitor.update(
            completed["features"]
        )

        drift_s3 = None

        if drift["drift_detected"]:
            drift_s3 = save_drift_event(
                completed["window_start"],
                drift,
            )

        prediction_payload = {
            "service": "RailGuard AI",
            "model_version": MODEL_CONFIG["version"],
            "timestamp": completed["window_start"],
            "reading_count": completed["reading_count"],
            "prediction": prediction,
            "runtime": runtime,
            "drift": drift,
        }

        prediction_s3 = save_prediction(
            completed["window_start"],
            prediction_payload,
        )

        response["prediction"] = prediction
        response["runtime"] = runtime
        response["maintenance_automation"] = maintenance_automation
        response["drift"] = drift
        response["drift_s3"] = drift_s3
        response["prediction_s3"] = prediction_s3

    return response

from collections import deque
from datetime import datetime
from statistics import mean, stdev

from app.model_service import required_features


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


class LiveFeatureEngine:

    def __init__(self):
        self.current_minute = None
        self.readings = []
        self.history = deque(maxlen=30)

    def _minute(self, timestamp):
        ts = datetime.fromisoformat(str(timestamp))
        return ts.replace(second=0, microsecond=0)

    def add_reading(self, timestamp, sensors):
        minute = self._minute(timestamp)

        if self.current_minute is None:
            self.current_minute = minute
            self.readings.append(sensors)

            return {
                "status": "buffering",
                "completed_window": None,
            }

        if minute == self.current_minute:
            self.readings.append(sensors)

            return {
                "status": "buffering",
                "completed_window": None,
            }

        if minute < self.current_minute:
            raise ValueError(
                "Sensor readings must arrive in timestamp order."
            )

        completed = self._finalize_window()

        self.current_minute = minute
        self.readings = [sensors]

        return {
            "status": "window_completed",
            "completed_window": completed,
        }

    def _finalize_window(self):
        features = {}

        for sensor in CONTINUOUS:
            values = [
                float(row[sensor])
                for row in self.readings
            ]

            features[f"{sensor}_mean"] = mean(values)
            features[f"{sensor}_std"] = (
                stdev(values)
                if len(values) > 1
                else 0.0
            )
            features[f"{sensor}_min"] = min(values)
            features[f"{sensor}_max"] = max(values)

        for sensor in BINARY:
            values = [
                float(row[sensor])
                for row in self.readings
            ]

            features[f"{sensor}_active_ratio"] = mean(values)

        current_means = {
            sensor: features[f"{sensor}_mean"]
            for sensor in CONTINUOUS
        }

        self.history.append(current_means)

        for sensor in CONTINUOUS:
            values = [
                row[sensor]
                for row in self.history
            ]

            rolling_mean = mean(values)

            rolling_std = (
                stdev(values)
                if len(values) > 1
                else 0.0
            )

            features[f"{sensor}_mean_30m_mean"] = rolling_mean
            features[f"{sensor}_mean_30m_std"] = rolling_std
            features[
                f"{sensor}_mean_vs_30m_mean"
            ] = (
                features[f"{sensor}_mean"]
                - rolling_mean
            )

        needed = required_features()

        missing = [
            feature
            for feature in needed
            if feature not in features
        ]

        if missing:
            raise ValueError(
                f"Live feature engine missing features: {missing}"
            )

        final_features = {
            feature: float(features[feature])
            for feature in needed
        }

        history_windows = len(self.history)

        return {
            "window_start": self.current_minute.isoformat(),
            "reading_count": len(self.readings),
            "features": final_features,
            "history_windows": history_windows,
            "ready_for_prediction": history_windows >= 30,
        }


feature_engine = LiveFeatureEngine()

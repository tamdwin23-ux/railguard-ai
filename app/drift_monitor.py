from collections import deque
from pathlib import Path
import json


BASE_DIR = Path(__file__).resolve().parent.parent

with open(
    BASE_DIR / "models" / "feature_baseline.json",
    "r",
) as file:
    BASELINE = json.load(file)["features"]


WINDOW_SIZE = 60
MIN_WINDOWS = 30
Z_THRESHOLD = 2.0
FEATURE_COUNT_THRESHOLD = 5


class DriftMonitor:
    def __init__(self):
        self.history = deque(maxlen=WINDOW_SIZE)

    def update(self, features):
        self.history.append(features)

        if len(self.history) < MIN_WINDOWS:
            return {
                "status": "warming_up",
                "windows": len(self.history),
                "required_windows": MIN_WINDOWS,
                "drift_detected": False,
            }

        shifts = []

        for feature, baseline in BASELINE.items():
            values = [
                float(row[feature])
                for row in self.history
                if feature in row
            ]

            if not values:
                continue

            recent_mean = sum(values) / len(values)

            baseline_mean = float(
                baseline["mean"]
            )

            baseline_std = max(
                float(baseline["std"]),
                1e-12,
            )

            z_shift = (
                recent_mean - baseline_mean
            ) / baseline_std

            shifts.append({
                "feature": feature,
                "recent_mean": recent_mean,
                "baseline_mean": baseline_mean,
                "z_shift": float(z_shift),
                "absolute_shift": abs(float(z_shift)),
            })

        shifts.sort(
            key=lambda item: item["absolute_shift"],
            reverse=True,
        )

        shifted_features = [
            item
            for item in shifts
            if item["absolute_shift"] >= Z_THRESHOLD
        ]

        drift_detected = (
            len(shifted_features)
            >= FEATURE_COUNT_THRESHOLD
        )

        return {
            "status": "ready",
            "windows": len(self.history),
            "drift_detected": drift_detected,
            "shifted_feature_count": len(
                shifted_features
            ),
            "top_shifts": shifts[:5],
        }


drift_monitor = DriftMonitor()

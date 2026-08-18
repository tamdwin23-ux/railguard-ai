from pathlib import Path
import json


BASE_DIR = Path(__file__).resolve().parent.parent
BASELINE_FILE = BASE_DIR / "models" / "feature_baseline.json"

with open(BASELINE_FILE, "r") as file:
    BASELINE = json.load(file)


def explain_features(feature_data, top_n=5):
    deviations = []

    for feature, value in feature_data.items():
        baseline = BASELINE["features"].get(feature)

        if baseline is None:
            continue

        mean = float(baseline["mean"])
        std = float(baseline["std"])

        if std <= 0:
            continue

        z_score = (float(value) - mean) / std

        deviations.append({
            "feature": feature,
            "value": float(value),
            "baseline_mean": mean,
            "z_score": float(z_score),
            "absolute_deviation": abs(float(z_score)),
            "direction": (
                "above_baseline"
                if z_score > 0
                else "below_baseline"
            ),
        })

    deviations.sort(
        key=lambda item: item["absolute_deviation"],
        reverse=True,
    )

    return {
        "method": "training_baseline_z_score",
        "top_deviations": deviations[:top_n],
    }

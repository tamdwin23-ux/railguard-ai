import pandas as pd
import numpy as np
import joblib

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score

DATA_FILE = "data/features_v2/metropt_features_trend_30min.csv"
MODEL_FILE = "models/regimes/kmeans_regime_v1.joblib"
RESULT_FILE = "results/regime_cluster_tests.csv"

TRAIN_END = pd.Timestamp("2020-04-01 00:00:00")

FEATURES = [
    "TP2_mean",
    "TP3_mean",
    "H1_mean",
    "DV_pressure_mean",
    "Reservoirs_mean",
    "Oil_temperature_mean",
    "Motor_current_mean",
    "COMP_active_ratio",
    "DV_eletric_active_ratio",
    "Towers_active_ratio",
    "MPG_active_ratio",
]

USECOLS = [
    "window_start",
    "is_failure",
    "failure_within_2h",
] + FEATURES

parts = []

for chunk in pd.read_csv(
    DATA_FILE,
    usecols=USECOLS,
    chunksize=50000,
    parse_dates=["window_start"],
):
    normal = chunk[
        (chunk["window_start"] < TRAIN_END)
        & (chunk["is_failure"] == 0)
        & (chunk["failure_within_2h"] == 0)
    ].copy()

    if not normal.empty:
        parts.append(normal)

train = pd.concat(parts, ignore_index=True)

print("Normal training windows:", len(train))
print("Regime features:", len(FEATURES))

X = train[FEATURES]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Small sample for silhouette calculation to keep EC2 usage low.
rng = np.random.RandomState(42)

sample_size = min(2000, len(X_scaled))

sample_indices = rng.choice(
    len(X_scaled),
    size=sample_size,
    replace=False,
)

X_silhouette = X_scaled[sample_indices]

results = []
models = {}

for k in range(2, 7):

    print("\nTesting", k, "regimes...")

    model = MiniBatchKMeans(
        n_clusters=k,
        batch_size=2048,
        random_state=42,
        n_init=10,
    )

    labels = model.fit_predict(X_scaled)

    sample_labels = labels[sample_indices]

    silhouette = silhouette_score(
        X_silhouette,
        sample_labels,
    )

    inertia = model.inertia_

    counts = pd.Series(labels).value_counts().sort_index()

    print("Silhouette score:", round(silhouette, 4))
    print("Inertia:", round(inertia, 2))
    print("Cluster sizes:")
    print(counts.to_string())

    results.append({
        "k": k,
        "silhouette_score": silhouette,
        "inertia": inertia,
        "smallest_cluster": int(counts.min()),
        "largest_cluster": int(counts.max()),
    })

    models[k] = model


results_df = pd.DataFrame(results)

best_k = int(
    results_df.loc[
        results_df["silhouette_score"].idxmax(),
        "k"
    ]
)

best_model = models[best_k]

print("\n====================")
print("BEST CANDIDATE")
print("====================")
print("Regimes:", best_k)

best_score = results_df.loc[
    results_df["k"] == best_k,
    "silhouette_score"
].iloc[0]

print("Silhouette score:", round(best_score, 4))

joblib.dump(
    {
        "model": best_model,
        "scaler": scaler,
        "features": FEATURES,
        "best_k": best_k,
        "train_end": TRAIN_END,
    },
    MODEL_FILE,
)

results_df.to_csv(
    RESULT_FILE,
    index=False,
)

print("\nModel saved:", MODEL_FILE)
print("Results saved:", RESULT_FILE)

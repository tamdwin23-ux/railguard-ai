import pandas as pd

INPUT_FILE = "results/hybrid_risk_states.csv"
OUTPUT_FILE = "results/railguard_risk_events_v3.csv"

FAULT_ANOMALY_MINUTES = 20
GAP_TOLERANCE_MINUTES = 2

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["window_start"]
)

df = df.sort_values("window_start").reset_index(drop=True)

events = []

# WATCH episodes
watch = df[
    (df["regime_anomaly"] == 1)
    & (df["global_anomaly"] == 0)
].copy()

if not watch.empty:
    watch_gap = (
        watch["window_start"].diff()
        > pd.Timedelta(minutes=1)
    )

    watch["episode_id"] = watch_gap.cumsum()

    watch_episodes = (
        watch.groupby("episode_id")
        .agg(
            start=("window_start", "min"),
            end=("window_start", "max"),
            minutes=("window_start", "count"),
        )
        .reset_index(drop=True)
    )

    for episode in watch_episodes.itertuples(index=False):
        events.append({
            "timestamp": episode.start,
            "event_type": "WATCH_EPISODE",
            "risk_level": "WATCH",
            "episode_start": episode.start,
            "episode_end": episode.end,
            "duration_minutes": episode.minutes,
            "anomaly_minutes": episode.minutes,
        })


# Global anomaly episodes
global_positive = df[
    df["global_anomaly"] == 1
].copy()

if not global_positive.empty:

    max_gap = pd.Timedelta(
        minutes=GAP_TOLERANCE_MINUTES + 1
    )

    new_episode = (
        global_positive["window_start"].diff()
        > max_gap
    )

    global_positive["episode_id"] = (
        new_episode.cumsum()
    )

    confirmed_fault_open = False
    incident_id = 0

    for _, episode in global_positive.groupby("episode_id"):

        episode = episode.sort_values("window_start")

        anomaly_minutes = len(episode)

        if anomaly_minutes < FAULT_ANOMALY_MINUTES:
            continue

        episode_start = episode["window_start"].iloc[0]
        episode_end = episode["window_start"].iloc[-1]

        confirm_time = episode[
            "window_start"
        ].iloc[FAULT_ANOMALY_MINUTES - 1]

        if not confirmed_fault_open:
            incident_id += 1

            events.append({
                "timestamp": confirm_time,
                "event_type": "CONFIRMED_FAULT",
                "risk_level": "CRITICAL",
                "incident_id": incident_id,
                "episode_start": episode_start,
                "episode_end": episode_end,
                "duration_minutes": int(
                    (
                        episode_end - episode_start
                    ).total_seconds() / 60
                ) + 1,
                "anomaly_minutes": anomaly_minutes,
            })

            confirmed_fault_open = True

        else:
            events.append({
                "timestamp": confirm_time,
                "event_type": "FAULT_UPDATE",
                "risk_level": "CRITICAL",
                "incident_id": incident_id,
                "episode_start": episode_start,
                "episode_end": episode_end,
                "duration_minutes": int(
                    (
                        episode_end - episode_start
                    ).total_seconds() / 60
                ) + 1,
                "anomaly_minutes": anomaly_minutes,
            })


events_df = pd.DataFrame(events)

if not events_df.empty:
    events_df = events_df.sort_values(
        "timestamp"
    ).reset_index(drop=True)

events_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("RailGuard Risk Engine V3 complete.")
print("Events created:", len(events_df))

if not events_df.empty:
    print("\nEvent counts:")
    print(events_df["event_type"].value_counts())

print("\nSaved:", OUTPUT_FILE)

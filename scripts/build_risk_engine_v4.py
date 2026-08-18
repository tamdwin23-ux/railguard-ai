import pandas as pd

INPUT_FILE = "results/hybrid_risk_states.csv"
OUTPUT_FILE = "results/railguard_risk_events_v4.csv"

FAULT_ANOMALY_MINUTES = 20
GAP_TOLERANCE_MINUTES = 2
INCIDENT_MERGE_MINUTES = 240
WATCH_MINUTES = 3

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["window_start"]
)

df = df.sort_values("window_start").reset_index(drop=True)

events = []

# -------------------------
# WATCH EPISODES
# -------------------------

watch = df[
    (df["regime_anomaly"] == 1)
    & (df["global_anomaly"] == 0)
].copy()

if not watch.empty:

    new_watch = (
        watch["window_start"].diff()
        > pd.Timedelta(minutes=1)
    )

    watch["episode_id"] = new_watch.cumsum()

    watch_episodes = (
        watch.groupby("episode_id")
        .agg(
            start=("window_start", "min"),
            end=("window_start", "max"),
            minutes=("window_start", "count"),
        )
        .reset_index(drop=True)
    )

    watch_episodes = watch_episodes[
        watch_episodes["minutes"] >= WATCH_MINUTES
    ]

    for episode in watch_episodes.itertuples(index=False):

        events.append({
            "timestamp": episode.start,
            "event_type": "WATCH_EPISODE",
            "risk_level": "WATCH",
            "incident_id": None,
            "episode_start": episode.start,
            "episode_end": episode.end,
            "duration_minutes": episode.minutes,
            "anomaly_minutes": episode.minutes,
            "status": "MONITOR",
        })


# -------------------------
# GLOBAL ANOMALY EPISODES
# -------------------------

global_positive = df[
    df["global_anomaly"] == 1
].copy()

confirmed = []

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

    for _, episode in global_positive.groupby("episode_id"):

        episode = episode.sort_values("window_start")

        anomaly_minutes = len(episode)

        if anomaly_minutes < FAULT_ANOMALY_MINUTES:
            continue

        start = episode["window_start"].iloc[0]
        end = episode["window_start"].iloc[-1]

        confirm_time = episode[
            "window_start"
        ].iloc[FAULT_ANOMALY_MINUTES - 1]

        confirmed.append({
            "start": start,
            "end": end,
            "confirm_time": confirm_time,
            "anomaly_minutes": anomaly_minutes,
        })


# -------------------------
# MERGE RELATED FAULTS
# -------------------------

merged = []

for episode in confirmed:

    if not merged:

        merged.append({
            "start": episode["start"],
            "end": episode["end"],
            "confirm_time": episode["confirm_time"],
            "anomaly_minutes": episode["anomaly_minutes"],
            "episode_count": 1,
        })

        continue

    previous = merged[-1]

    gap = (
        episode["start"]
        - previous["end"]
    )

    if gap <= pd.Timedelta(
        minutes=INCIDENT_MERGE_MINUTES
    ):

        previous["end"] = max(
            previous["end"],
            episode["end"]
        )

        previous["anomaly_minutes"] += (
            episode["anomaly_minutes"]
        )

        previous["episode_count"] += 1

    else:

        merged.append({
            "start": episode["start"],
            "end": episode["end"],
            "confirm_time": episode["confirm_time"],
            "anomaly_minutes": episode["anomaly_minutes"],
            "episode_count": 1,
        })


# -------------------------
# CREATE INCIDENT EVENTS
# -------------------------

for incident_id, incident in enumerate(
    merged,
    start=1
):

    duration = int(
        (
            incident["end"]
            - incident["start"]
        ).total_seconds() / 60
    ) + 1

    events.append({
        "timestamp": incident["confirm_time"],
        "event_type": "CONFIRMED_FAULT",
        "risk_level": "CRITICAL",
        "incident_id": incident_id,
        "episode_start": incident["start"],
        "episode_end": incident["end"],
        "duration_minutes": duration,
        "anomaly_minutes": incident["anomaly_minutes"],
        "status": "OPEN",
    })


# -------------------------
# SAVE
# -------------------------

events_df = pd.DataFrame(events)

if not events_df.empty:

    events_df = events_df.sort_values(
        "timestamp"
    ).reset_index(drop=True)

events_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("RailGuard Risk Engine V4 complete.")
print("Events created:", len(events_df))

if not events_df.empty:

    print("\nEvent counts:")
    print(events_df["event_type"].value_counts())

    print(
        "\nConfirmed fault incidents:",
        len(
            events_df[
                events_df["event_type"]
                == "CONFIRMED_FAULT"
            ]
        )
    )

    print(
        "WATCH episodes:",
        len(
            events_df[
                events_df["event_type"]
                == "WATCH_EPISODE"
            ]
        )
    )

print("\nSaved:", OUTPUT_FILE)

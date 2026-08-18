import pandas as pd

INPUT_FILE = "results/hybrid_risk_states.csv"
OUTPUT_FILE = "results/railguard_risk_events.csv"

# Evidence-based rule from our testing:
# 20 consecutive global-anomaly 1-minute windows
# = confirmed fault condition.
FAULT_PERSISTENCE = 20

events = []

global_streak = 0
episode_start = None
last_timestamp = None
fault_open = False

for chunk in pd.read_csv(
    INPUT_FILE,
    chunksize=50000,
    parse_dates=["window_start"],
):
    chunk = chunk.sort_values("window_start")

    for row in chunk.itertuples(index=False):

        timestamp = row.window_start
        global_anomaly = int(row.global_anomaly)
        regime_anomaly = int(row.regime_anomaly)

        # Detect large data gaps.
        if last_timestamp is not None:
            gap = timestamp - last_timestamp

            if gap > pd.Timedelta(minutes=2):
                global_streak = 0
                episode_start = None
                fault_open = False

        # --------------------------------
        # GLOBAL ANOMALY / FAULT TRACKING
        # --------------------------------
        if global_anomaly == 1:

            if global_streak == 0:
                episode_start = timestamp

            global_streak += 1

            # Confirm fault after 20 persistent
            # abnormal 1-minute windows.
            if (
                global_streak >= FAULT_PERSISTENCE
                and not fault_open
            ):
                events.append({
                    "timestamp": timestamp,
                    "event_type": "CONFIRMED_FAULT",
                    "risk_level": "CRITICAL",
                    "episode_start": episode_start,
                    "global_streak": global_streak,
                    "global_anomaly": global_anomaly,
                    "regime_anomaly": regime_anomaly,
                })

                fault_open = True

        else:

            # If a confirmed fault episode ends,
            # record its recovery.
            if fault_open:
                events.append({
                    "timestamp": timestamp,
                    "event_type": "FAULT_CLEARED",
                    "risk_level": "LOW",
                    "episode_start": episode_start,
                    "global_streak": global_streak,
                    "global_anomaly": global_anomaly,
                    "regime_anomaly": regime_anomaly,
                })

            global_streak = 0
            episode_start = None
            fault_open = False

            # --------------------------------
            # EARLY DEGRADATION SIGNAL
            # --------------------------------
            if regime_anomaly == 1:
                events.append({
                    "timestamp": timestamp,
                    "event_type": "WATCH",
                    "risk_level": "WATCH",
                    "episode_start": timestamp,
                    "global_streak": 0,
                    "global_anomaly": 0,
                    "regime_anomaly": 1,
                })

        last_timestamp = timestamp


events_df = pd.DataFrame(events)

events_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("Risk engine complete.")
print("Events created:", len(events_df))

if not events_df.empty:
    print("\nEvent counts:")
    print(events_df["event_type"].value_counts())

print("\nSaved:", OUTPUT_FILE)

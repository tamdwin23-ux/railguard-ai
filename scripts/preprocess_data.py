import pandas as pd

INPUT_FILE = "data/raw/MetroPT3(AirCompressor).csv"
OUTPUT_FILE = "data/processed/metropt_clean.csv"

FAILURES = [
    ("2020-04-18 00:00:00", "2020-04-18 23:59:59"),
    ("2020-05-29 23:30:00", "2020-05-30 06:00:00"),
    ("2020-06-05 10:00:00", "2020-06-07 14:30:00"),
    ("2020-07-15 14:30:00", "2020-07-15 19:00:00"),
]

first_chunk = True

for chunk in pd.read_csv(INPUT_FILE, chunksize=100000):

    chunk = chunk.drop(columns=["Unnamed: 0"])

    chunk["timestamp"] = pd.to_datetime(chunk["timestamp"])

    chunk["is_failure"] = 0
    chunk["failure_within_2h"] = 0

    for start, end in FAILURES:
        start = pd.Timestamp(start)
        end = pd.Timestamp(end)

        failure_mask = (
            (chunk["timestamp"] >= start) &
            (chunk["timestamp"] <= end)
        )

        prefailure_mask = (
            (chunk["timestamp"] >= start - pd.Timedelta(hours=2)) &
            (chunk["timestamp"] < start)
        )

        chunk.loc[failure_mask, "is_failure"] = 1
        chunk.loc[prefailure_mask, "failure_within_2h"] = 1

    chunk.to_csv(
        OUTPUT_FILE,
        mode="w" if first_chunk else "a",
        header=first_chunk,
        index=False
    )

    first_chunk = False

print("Preprocessing complete.")

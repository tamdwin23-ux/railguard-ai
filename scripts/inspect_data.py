import pandas as pd

file_path = "data/raw/MetroPT3(AirCompressor).csv"

columns = [
    "index",
    "timestamp",
    "TP2",
    "TP3",
    "H1",
    "DV_pressure",
    "Reservoirs",
    "Oil_temperature",
    "Motor_current",
    "COMP",
    "DV_electric",
    "TOWERS",
    "MPG",
    "LPS",
    "Pressure_switch",
    "Oil_level",
    "Caudal_impulse",
]

df = pd.read_csv(
    file_path,
    header=0,
    nrows=10000
)

print("Dataset shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head())

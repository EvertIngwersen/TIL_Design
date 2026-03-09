# -*- coding: utf-8 -*-
from pathlib import Path
import pyarrow.parquet as pq

# Current script directory
BASE_DIR = Path(__file__).resolve().parent

# Relative path to the parquet file
parquet_file = BASE_DIR.parent / "Large Data" / "flight_events" / "flight_events_20240101_20240111.parquet"

print("Scanning parquet file from:", parquet_file)

# Open the parquet file as a PyArrow Table
table = pq.read_table(parquet_file, columns=["flight_id", "timestamp", "lat", "lon"])

# Convert to Pandas DataFrame if needed
df = table.to_pandas()

# Inspect first rows
print(df.head())
print(df.info())


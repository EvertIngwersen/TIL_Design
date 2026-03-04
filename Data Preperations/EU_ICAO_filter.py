# -*- coding: utf-8 -*-
"""
Filter EU airports (small, medium, large only)
"""

import pandas as pd

# -------- FILE PATHS -------- #

input_path = r"C:\Users\evert\Documents\TU-Delft\TIL Master\TIL5050-20 TIL Design Project\TIL_Design_Repo\TIL_Design\Data\Flight Data\airports_list_full.csv"

output_path = r"C:\Users\evert\Documents\TU-Delft\TIL Master\TIL5050-20 TIL Design Project\TIL_Design_Repo\TIL_Design\Data\Flight Data\EU_Airports_List.csv"


# -------- LOAD DATA -------- #

df = pd.read_csv(input_path)


# -------- FILTER CONDITIONS -------- #

allowed_types = ["medium_airport", "large_airport"]

eu_airports = df[
    (df["continent"].str.strip() == "EU") &
    (df["type"].isin(allowed_types))
]


# -------- SAVE FILTERED DATA -------- #

eu_airports.to_csv(output_path, index=False)


# -------- CONFIRMATION -------- #

print(f"Total airports in dataset: {len(df)}")
print(f"Total EU airports (small/medium/large): {len(eu_airports)}")
print("Filtered EU airport list successfully saved.")

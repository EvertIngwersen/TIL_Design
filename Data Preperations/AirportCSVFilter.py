"""
Created on Fri Feb 13 13:32:10 2026

@author: evert
"""

import pandas as pd
import os

# ---------- FILE PATHS ---------- #

input_path = r"C:\Users\evert\Documents\TU-Delft\TIL Master\TIL5050-20 TIL Design Project\TIL_Design_Repo\TIL_Design\Data\Flight Data\OD Data\merged_OD_data.csv"

output_path = r"C:\Users\evert\Documents\TU-Delft\TIL Master\TIL5050-20 TIL Design Project\TIL_Design_Repo\TIL_Design\Data\Flight Data\OD Data\merged_OD_data_EU_only.csv"


# ---------- LOAD DATA ---------- #

df = pd.read_csv(input_path)

print(f"Original rows: {len(df)}")


# ---------- FUNCTION TO CHECK ICAO ---------- #

def is_european_route(airp_pr):
    try:
        parts = airp_pr.split("_")

        icao1 = parts[1]
        icao2 = parts[3]

        allowed_prefixes = ("E", "L", "B")

        # Check allowed prefixes
        valid_icao1 = icao1.startswith(allowed_prefixes) and not icao1.startswith("LL")
        valid_icao2 = icao2.startswith(allowed_prefixes) and not icao2.startswith("LL")

        return valid_icao1 and valid_icao2

    except:
        return False


# ---------- APPLY FILTER ---------- #

df_filtered = df[df["airp_pr"].apply(is_european_route)]

print(f"Filtered rows: {len(df_filtered)}")


# ---------- SAVE RESULT ---------- #

df_filtered.to_csv(output_path, index=False)

print("European-only airport file saved successfully!")

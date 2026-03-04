# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 16:55:07 2026

@author: evert
"""

# -*- coding: utf-8 -*-
"""
Match airport_names.csv with EU_Airports_List.csv
and extract corresponding ICAO codes using built-in difflib
"""

import pandas as pd
import difflib

# -------- FILE PATHS -------- #

airport_names_path = r"C:\Users\evert\Documents\TU-Delft\TIL Master\TIL5050-20 TIL Design Project\TIL_Design_Repo\TIL_Design\Data\Flight Data\airport_names.csv"

eu_airports_path = r"C:\Users\evert\Documents\TU-Delft\TIL Master\TIL5050-20 TIL Design Project\TIL_Design_Repo\TIL_Design\Data\Flight Data\EU_Airports_List.csv"

output_path = r"C:\Users\evert\Documents\TU-Delft\TIL Master\TIL5050-20 TIL Design Project\TIL_Design_Repo\TIL_Design\Data\Flight Data\Matched_EU_Airports_With_ICAO.csv"


# -------- LOAD DATA -------- #

airport_names_df = pd.read_csv(airport_names_path, header=None, names=["original_name"])
eu_airports_df = pd.read_csv(eu_airports_path)


# -------- CLEAN STRINGS FUNCTION -------- #

def clean_name(name):
    name = str(name).upper()
    name = name.replace("AIRPORT", "")
    name = name.replace("/", " ")
    name = name.strip()
    return name


airport_names_df["clean_name"] = airport_names_df["original_name"].apply(clean_name)
eu_airports_df["clean_name"] = eu_airports_df["name"].apply(clean_name)

eu_name_list = eu_airports_df["clean_name"].tolist()


# -------- MATCHING USING DIFFLIB -------- #

matched_names = []
matched_icao = []
match_scores = []

for name in airport_names_df["clean_name"]:
    
    matches = difflib.get_close_matches(name, eu_name_list, n=1, cutoff=0.6)
    
    if matches:
        best_match = matches[0]
        index = eu_name_list.index(best_match)
        
        matched_names.append(eu_airports_df.iloc[index]["name"])
        matched_icao.append(eu_airports_df.iloc[index]["ident"])
        
        # similarity score (0-1 scale)
        score = difflib.SequenceMatcher(None, name, best_match).ratio()
        match_scores.append(round(score * 100, 1))
        print("Match found")
    else:
        matched_names.append(None)
        matched_icao.append(None)
        match_scores.append(0)
        print("No match")


# -------- CREATE RESULT DATAFRAME -------- #

result_df = airport_names_df.copy()
result_df["matched_name"] = matched_names
result_df["icao_code"] = matched_icao
result_df["match_score_%"] = match_scores

result_df = result_df.drop(columns=["clean_name"])


# -------- SAVE RESULT -------- #

result_df.to_csv(output_path, index=False)

print("Matching completed.")
print(f"Results saved to: {output_path}")

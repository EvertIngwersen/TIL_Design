# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 15:51:26 2026

@author: evert
"""

import os
import pandas as pd

# Get directory of this script
base_dir = os.path.dirname(os.path.abspath(__file__))

file_path = os.path.join(
    base_dir,
    "Data",
    "Flight Data",
    "avia_paoa__custom_20087840_spreadsheet.xlsx"
)

df = pd.read_excel(
    file_path,
    sheet_name="Sheet 1",
    usecols="A",
    skiprows=12,
    nrows=870
)

airport_names = df.iloc[:, 0].dropna().tolist()

print(airport_names[:10])
print(f"Total airports loaded: {len(airport_names)}")

save_path = r"C:\Users\evert\Documents\TU-Delft\TIL Master\TIL5050-20 TIL Design Project\TIL_Design_Repo\TIL_Design\Data\Flight Data\airport_names.csv"

pd.DataFrame(airport_names, columns=["Airport"]).to_csv(
    save_path,
    index=False
)

print("Airport list saved as CSV.")



































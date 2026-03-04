# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 13:31:23 2026

@author: evert
"""

import pandas as pd
import glob
import os

# Folder containing your CSV files
folder_path = r"C:\Users\evert\Documents\TU-Delft\TIL Master\TIL5050-20 TIL Design Project\TIL_Design_Repo\TIL_Design\Data\Flight Data\OD Data"

# Get all CSV files in the folder
csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

print(f"Found {len(csv_files)} CSV files.")

# Read and combine all CSVs
df_list = [pd.read_csv(file) for file in csv_files]

# Concatenate vertically (stack below each other)
merged_df = pd.concat(df_list, ignore_index=True)

# Save to new CSV
output_path = os.path.join(folder_path, "merged_OD_data.csv")
merged_df.to_csv(output_path, index=False)

print("All files successfully merged!")

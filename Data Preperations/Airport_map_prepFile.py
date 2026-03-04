"""
Created on Sun Feb 15 12:19:22 2026

@author: evert
"""
print("Loading libraries...")
import pandas as pd
import os
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
import json
print("Libraries loaded")

# Force Plotly to open figures in your default browser
pio.renderers.default = "browser"

print(os.getcwd())

# --- Load data ---
OD_data = pd.read_csv("../Data/Flight Data/OD Data/merged_OD_data_EU_only.csv")
Aiport_data_full = pd.read_csv("../Data/Flight Data/airports_list_full.csv")
print("")
print("Airport data loaded")

# --- Filter for passenger data ---
passengers_data = OD_data[OD_data['tra_meas'] == 'PAS'].copy()

# --- Extract ICAO codes from OD pairs ---
icao_set = set()
for pair in OD_data["airp_pr"]:
    parts = pair.split("_")
    icao_set.add(parts[1])
    icao_set.add(parts[3])

ICAO_codes = sorted(list(icao_set))
print(f"Number of unique ICAO codes: {len(ICAO_codes)}")

# --- Filter full dataset to only the ICAO codes you need ---
filtered_airports = Aiport_data_full[Aiport_data_full["ident"].isin(ICAO_codes)]

# --- Create dictionary of airport locations ---
Airports_locations = {
    row["ident"]: (row["latitude_deg"], row["longitude_deg"])
    for _, row in filtered_airports.iterrows()
}
print(f"Number of matched airports: {len(Airports_locations)}")

# --- Find missing airports ---
matched_codes = set(Airports_locations.keys())
missing_codes = sorted(set(ICAO_codes) - matched_codes)
print(f"Number of missing airports: {len(missing_codes)}")
print("Missing ICAO codes:", missing_codes)

# --- MANUAL ADDITIONS ---
manual_airports = {
    "EDDT": (52.34, 13.17),   
    "EG40": (51.984986, -1.065159),
    "EGCN": (53.28, 1.00),   
    "EGPM": (60.25, 1.17),
    "LKAA": (50.600, 14.16),   # LKAA is Prague FIR → use LKPR airport location instead
    "LPPO": (38.45, 27.050),   # LPPO is Madeira FIR → use LPLA airport location instead
    "LTBB": (41.15, 28.43)     # LTBB is Istanbul FIR → use LTFM airport location instead
}


Airports_locations.update(manual_airports)
print(f"Total airports after manual additions: {len(Airports_locations)}")

# --- Convert dictionary to DataFrame ---
airport_df = pd.DataFrame(
    [(icao, lat, lon) for icao, (lat, lon) in Airports_locations.items()],
    columns=["ICAO", "Latitude", "Longitude"]
)

# --- Select only needed columns from full airport dataset ---
airport_names = Aiport_data_full[["ident", "name"]].copy()

# --- Merge names into airport_df ---
airport_df = airport_df.merge(
    airport_names,
    left_on="ICAO",
    right_on="ident",
    how="left"
)

# --- Drop duplicate column and rename ---
airport_df = airport_df.drop(columns=["ident"])
airport_df = airport_df.rename(columns={"name": "Airport_Name"})


# --- MANUAL NAMES ---
manual_names = {
    "EDDT": "Berlin-Tegel Airport",
    "EG40": "Finmere Airport",
    "EGCN": "Doncaster-Sheffield Airport",
    "EGPM": "Scatsta Airport",
    "LKAA": "Prague FIR",
    "LPPO": "Santa Maria Oceanic Area Control Centre FIR",
    "LTBB": "Istanbul FIR"
}

# Fill or overwrite names for manual airports
airport_df["Airport_Name"] = airport_df.apply(
    lambda row: manual_names.get(row["ICAO"], row["Airport_Name"]),
    axis=1
)

for icao, (lat, lon) in manual_airports.items():
    if icao not in airport_df["ICAO"].values:
        airport_df = pd.concat([
            airport_df,
            pd.DataFrame([{
                "ICAO": icao,
                "Latitude": lat,
                "Longitude": lon,
                "Airport_Name": manual_names.get(icao, None)
            }])
        ], ignore_index=True)

print("Airport names added.")
print(airport_df.head())
print(airport_df[airport_df["ICAO"].isin(manual_names.keys())])

# --- Save airport dataframe ---
output_path = "../Data/Flight Data/airport_locations_with_names.csv"

airport_df.to_csv(output_path, index=False)

print(f"Airport dataframe saved to: {output_path}")

# #============== CREATING MAP ==================================================
# print("")
# print("Creating map...")
# # --- Load high-resolution GeoJSON ---
# print("")
# print("Loading map JSON vector data...")
# geojson_path = r"C:\Users\evert\Documents\TU-Delft\TIL Master\TIL5050-20 TIL Design Project\TIL_Design_Repo\TIL_Design\Data\Other Data\countries-land-1m.geo.json"
# with open(geojson_path, encoding="utf-8") as f:
#     world_geojson = json.load(f)
# print("JSON vector data loaded!")
# print("")
# print("Creating map...")
# # --- Create high-res map using the new Plotly API ---
# fig = px.choropleth_map(
#     geojson=world_geojson,
#     locations=[f.get("id", idx) for idx, f in enumerate(world_geojson["features"])],
#     color=[1]*len(world_geojson["features"]),  # dummy values
#     center={"lat": 54, "lon": 10},
#     zoom=3,
#     opacity=1
# )

# # Add airports using the new scatter map function
# fig.add_trace(go.Scattermap(
#     lon=airport_df['Longitude'],
#     lat=airport_df['Latitude'],
#     text=airport_df['ICAO'],
#     mode='markers',
#     marker=dict(size=6, color='red')
# ))

# fig.update_layout(
#     title="European Airports on High-Res World Map",
#     height=600,
#     margin={"r":0,"t":50,"l":0,"b":0}
# )

# fig.show()




# -*- coding: utf-8 -*-
"""
Created on Sun Feb 15 15:04:59 2026

@author: evert
"""
import pandas as pd
import os
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
import json


# Force Plotly to open figures in your default browser
pio.renderers.default = "browser"

# --- Load airport names  and locations---
airport_df = pd.read_csv("../Data/Flight Data/airport_locations_with_names.csv")

OD_matrix_flights = pd.read_csv(
    "../Data/Flight Data/OD Data/OD_matrix_flights.csv",
    index_col=0
)

OD_matrix_passengers = pd.read_csv(
    "../Data/Flight Data/OD Data/OD_matrix_passengers.csv",
    index_col=0
)

print("Computing airport statistics...")

airport_stats = []

for icao in airport_df["ICAO"]:
    
    # --- Flights ---
    total_departure_flights = OD_matrix_flights.loc[icao].sum() if icao in OD_matrix_flights.index else 0
    total_arrival_flights = OD_matrix_flights[icao].sum() if icao in OD_matrix_flights.columns else 0
    total_flights = total_departure_flights + total_arrival_flights
    
    # --- Passengers ---
    total_departure_pass = OD_matrix_passengers.loc[icao].sum() if icao in OD_matrix_passengers.index else 0
    total_arrival_pass = OD_matrix_passengers[icao].sum() if icao in OD_matrix_passengers.columns else 0
    total_passengers = total_departure_pass + total_arrival_pass
    
    # --- Destinations (unique connected airports, both directions) ---
    destinations = set()
    
    # Outgoing connections
    if icao in OD_matrix_flights.index:
        outgoing = OD_matrix_flights.loc[icao]
        destinations.update(outgoing[outgoing > 0].index)
    
    # Incoming connections
    if icao in OD_matrix_flights.columns:
        incoming = OD_matrix_flights[icao]
        destinations.update(incoming[incoming > 0].index)
    
    # Remove itself if present
    destinations.discard(icao)
    
    total_destinations = len(destinations)
    
    airport_stats.append([
    total_flights,
    total_passengers,
    total_destinations
])

    
airport_stats_df = pd.DataFrame(
    airport_stats,
    columns=["Total_Flights", "Total_Passengers", "Total_Destinations"]
)

airport_df = pd.concat([airport_df, airport_stats_df], axis=1)

print("Airport statistics computed.")

print("Computing top 5 busiest bidirectional routes...")

# Convert OD matrix to long format
od_long = (
    OD_matrix_flights
    .stack()
    .reset_index()
)
od_long.columns = ["Origin", "Destination", "Flights"]

# Remove zero flights and self-loops
od_long = od_long[(od_long["Flights"] > 0) & (od_long["Origin"] != od_long["Destination"])]

# Create a "sorted pair" column to treat A→B and B→A the same
od_long["Route"] = od_long.apply(lambda x: "-".join(sorted([x["Origin"], x["Destination"]])), axis=1)

# Aggregate flights per bidirectional route
od_agg = od_long.groupby("Route")["Flights"].sum().reset_index()

# Split Route back into Origin/Destination (first/second alphabetically)
od_agg[["Origin", "Destination"]] = od_agg["Route"].str.split("-", expand=True)

# Get top 5 busiest routes
top5_routes = od_agg.sort_values("Flights", ascending=False).head(5)

print(top5_routes[["Origin", "Destination", "Flights"]])



#============== CREATING MAP ==================================================
print("")
print("Creating map...")
# --- Load high-resolution GeoJSON ---
print("")
print("Loading map JSON vector data...")
geojson_path = r"C:\Users\evert\Documents\TU-Delft\TIL Master\TIL5050-20 TIL Design Project\TIL_Design_Repo\TIL_Design\Data\Other Data\countries-land-1m.geo.json"
with open(geojson_path, encoding="utf-8") as f:
    world_geojson = json.load(f)
print("JSON vector data loaded!")
print("")
print("Creating map...")

# --- Create high-res map using the new Plotly API ---
fig = px.choropleth_map(
    geojson=world_geojson,
    locations=[f.get("id", idx) for idx, f in enumerate(world_geojson["features"])],
    color=[1]*len(world_geojson["features"]),  # dummy values
    center={"lat": 54, "lon": 10},
    zoom=3,
    opacity=1
)

# Add airports using the new scatter map function
fig.add_trace(go.Scattermap(
    lon=airport_df['Longitude'],
    lat=airport_df['Latitude'],
    mode='markers',
    marker=dict(size=6, color='red'),
    
    customdata=airport_df[[
        'ICAO',
        'Airport_Name',
        'Total_Flights',
        'Total_Passengers',
        'Total_Destinations'
    ]].values,
    
    hovertemplate=
        "<b>%{customdata[0]}</b><br>" +
        "%{customdata[1]}<br><br>" +
        "<b>Total Flights:</b> %{customdata[2]:,.0f}<br>" +
        "<b>Total Passengers:</b> %{customdata[3]:,.0f}<br>" +
        "<b>Total Destinations:</b> %{customdata[4]}<br>" +
        "<extra></extra>"
))

# --- Add top 5 busiest bidirectional routes ---
print("Adding top 5 bidirectional routes to map...")

for _, row in top5_routes.iterrows():
    origin = row["Origin"]
    destination = row["Destination"]
    flights = row["Flights"]
    
    origin_data = airport_df[airport_df["ICAO"] == origin]
    dest_data = airport_df[airport_df["ICAO"] == destination]
    
    if origin_data.empty or dest_data.empty:
        continue
    
    lon = [origin_data["Longitude"].values[0],
           dest_data["Longitude"].values[0]]
    lat = [origin_data["Latitude"].values[0],
           dest_data["Latitude"].values[0]]
    
    fig.add_trace(go.Scattermap(
        lon=lon,
        lat=lat,
        mode="lines",
        line=dict(width=flights / top5_routes["Flights"].max() * 8, color="blue"),
        hovertemplate=
            f"<b>{origin} ↔ {destination}</b><br>" +
            f"Total Flights (both directions): {flights:,.0f}<br>" +
            "<extra></extra>"
    ))

# Finally, show the map
fig.show()


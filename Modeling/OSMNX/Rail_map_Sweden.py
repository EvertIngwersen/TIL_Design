# -*- coding: utf-8 -*-
"""
Sweden rail network:
- plots edges colored by maxspeed
- finds fastest route between any two Swedish cities (user input)
- compatible with latest OSMnx and Plotly
"""

import json
import numpy as np
import os
import osmnx as ox
import networkx as nx
import plotly.graph_objects as go
import plotly.io as pio
from pathlib import Path


pio.renderers.default = "browser"

# -----------------------------
# Load graph
# -----------------------------
# Get directory of this script
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent

graph_path = PROJECT_ROOT / "Data" / "Rail Data" / "Sweden_rail.graphml"

# Load graph
G = ox.load_graphml(graph_path)

# Convert to GeoDataFrames
nodes, edges = ox.graph_to_gdfs(G)
edges = edges.to_crs(epsg=4326)

# -----------------------------
# Clean maxspeed column
# -----------------------------
if "maxspeed" in edges.columns:
    edges["maxspeed"] = (
        edges["maxspeed"]
        .astype(str)
        .str.extract(r"(\d+)")  # numeric part only
        .astype(float)
    )
else:
    edges["maxspeed"] = np.nan

# -----------------------------
# Compute travel time (seconds)
# -----------------------------
edges["travel_time"] = edges["length"] / (edges["maxspeed"] * (1000/3600))

# Replace infinite / NaN travel times (missing maxspeed)
edges["travel_time"] = edges["travel_time"].replace([np.inf, -np.inf], np.nan)
edges["travel_time"] = edges["travel_time"].fillna(
    edges["length"] / (100 * (1000/3600))  # assume 100 km/h fallback
)

# Rebuild graph with travel_time attribute
G = ox.graph_from_gdfs(nodes, edges)

# -----------------------------
# Load Swedish city database
# -----------------------------
city_file = PROJECT_ROOT / "Data" / "Other Data" / "se_city_data" / "se" / "place_city.ndjson"

cities = {}
with open(city_file, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        name = data["name"].lower()
        coords = data["location"]  # [lon, lat]
        cities[name] = coords

# -----------------------------
# Ask user for origin/destination
# -----------------------------
def get_city_coordinates(prompt):
    while True:
        city_name = input(prompt).strip().lower()
        if city_name in cities:
            lon, lat = cities[city_name]
            return lat, lon
        else:
            print(f"City '{city_name}' not found in database. Try again.")

print("Available cities:", ", ".join(list(cities.keys())))
lat1, lon1 = get_city_coordinates("Enter origin city: ")
lat2, lon2 = get_city_coordinates("Enter destination city: ")

# Find nearest nodes in the graph
origin = ox.distance.nearest_nodes(G, X=lon1, Y=lat1)
destination = ox.distance.nearest_nodes(G, X=lon2, Y=lat2)

# -----------------------------
# Shortest path (fastest by travel_time)
# -----------------------------
if not nx.has_path(G, origin, destination):
    for comp in nx.connected_components(G.to_undirected()):
        if origin in comp and destination in comp:
            G_sub = G.subgraph(comp).copy()
            print("Using connected subgraph for path computation.")
            route = nx.shortest_path(G_sub, origin, destination, weight="travel_time")
            break
    else:
        raise ValueError("No connected path between the selected cities in the rail graph.")
else:
    route = nx.shortest_path(G, origin, destination, weight="travel_time")

# -----------------------------
# Plot network colored by maxspeed
# -----------------------------
fig = go.Figure()

speed_classes = edges["maxspeed"].dropna().unique()

for speed in sorted(speed_classes):
    subset = edges[edges["maxspeed"] == speed]
    lons, lats = [], []

    for geom in subset.geometry:
        if geom is not None:
            x, y = geom.xy
            lons.extend(x)
            lats.extend(y)
            lons.append(None)
            lats.append(None)

    fig.add_trace(go.Scattermap(
        lon=lons,
        lat=lats,
        mode="lines",
        line=dict(width=2),
        name=f"{int(speed)} km/h",
        hoverinfo="text",
        text=[f"Max speed: {speed} km/h"] * len(lons)
    ))

# -----------------------------
# Highlight fastest route in red
# -----------------------------
route_geoms = []

for u, v in zip(route[:-1], route[1:]):
    edge_data = G.get_edge_data(u, v)
    if edge_data:
        first_key = list(edge_data.keys())[0]
        geom = edge_data[first_key].get("geometry")
        if geom is not None:
            route_geoms.append(geom)

lons, lats = [], []

for geom in route_geoms:
    x, y = geom.xy
    lons.extend(x)
    lats.extend(y)
    lons.append(None)
    lats.append(None)

fig.add_trace(go.Scattermap(
    lon=lons,
    lat=lats,
    mode="lines",
    line=dict(width=4, color="red"),
    name="Fastest route"
))

# -----------------------------
# Layout (centered on Sweden)
# -----------------------------
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=5,
    mapbox_center={"lat": 62.0, "lon": 15.0},
    height=900,
    margin=dict(r=0, t=0, l=0, b=0)
)

fig.show()
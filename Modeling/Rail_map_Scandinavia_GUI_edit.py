# -*- coding: utf-8 -*-
"""
Scandinavia rail network (GUI-ready)
- Computes fastest route between DK, SE, NO cities
- Intermediate stops possible
- Opens Plotly map in browser
- Prints only route summary for GUI consumption
"""

import sys
import json
import unicodedata
import osmnx as ox
import numpy as np
import networkx as nx
import plotly.graph_objects as go
import plotly.io as pio
from pathlib import Path
from shapely.geometry import LineString

# -----------------------------
# GUI / CLI arguments
# -----------------------------
if len(sys.argv) >= 3:
    origin_input = sys.argv[1]
    destination_input = sys.argv[2]
    via_inputs = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] else []
else:
    raise ValueError("Please provide at least origin and destination as command-line arguments.")

# -----------------------------
# Parameters
# -----------------------------
STOP_TIME = 3 * 60  # dwell time per stop in seconds

manual_edges = [
    ("Øresund bridge", 55.5990688, 12.7514874, 55.5655404, 12.9042758, 200),
    ("Skottesjon - Ed", 58.9188632, 11.7195089, 58.9128502, 11.9275408, 120),
    ("Glasbruk - Charlottenberg", 59.9135771, 12.2852937, 59.887603, 12.2936895, 160),
    ("Tevelden - Storlien", 63.3264157, 12.0628143, 63.3172724, 12.0947319, 80),
    ("Hell - Stjordal", 63.4462156, 10.9000683, 63.4460545, 10.9063916, 60),
    ("Kolsan - Nes", 63.6527907, 11.0889117, 63.6538856, 11.0923136, 80),
    ("Riksgranan - Vassejavri", 68.4266175, 18.1207193, 68.4302478, 18.2516029, 80)
]

pio.renderers.default = "browser"

# -----------------------------
# Load graphs
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

dk_path = PROJECT_ROOT / "Data" / "Rail Data" / "Denmark_rail.graphml"
se_path = PROJECT_ROOT / "Data" / "Rail Data" / "Sweden_rail.graphml"
no_path = PROJECT_ROOT / "Data" / "Rail Data" / "Norway_rail.graphml"

G_dk = ox.load_graphml(dk_path)
G_se = ox.load_graphml(se_path)
G_no = ox.load_graphml(no_path)

# Offset node IDs to avoid collisions
G_se = nx.relabel_nodes(G_se, lambda x: x + max(G_dk.nodes) + 1)
G = nx.compose(G_dk, G_se)
G_no = nx.relabel_nodes(G_no, lambda x: x + max(G.nodes) + 1)
G = nx.compose(G, G_no)

# Convert to GeoDataFrames
nodes, edges = ox.graph_to_gdfs(G)
edges = edges.to_crs(epsg=4326)

# Clean maxspeed
if "maxspeed" in edges.columns:
    edges["maxspeed"] = edges["maxspeed"].astype(str).str.extract(r"(\d+)").astype(float)
else:
    edges["maxspeed"] = np.nan

# Compute travel time (seconds)
edges["travel_time"] = edges["length"] / (edges["maxspeed"] * (1000/3600))
edges["travel_time"] = edges["travel_time"].replace([np.inf, -np.inf], np.nan)
edges["travel_time"] = edges["travel_time"].fillna(edges["length"] / (100 * (1000/3600)))
G = ox.graph_from_gdfs(nodes, edges)

# -----------------------------
# Function to add manual edges
# -----------------------------
def add_manual_connection(G, lat1, lon1, lat2, lon2, speed_kmh):
    node_a = ox.distance.nearest_nodes(G, X=lon1, Y=lat1)
    node_b = ox.distance.nearest_nodes(G, X=lon2, Y=lat2)
    length = ox.distance.great_circle(lat1, lon1, lat2, lon2)
    travel_time = length / (speed_kmh * (1000/3600))
    geom = LineString([(lon1, lat1), (lon2, lat2)])
    G.add_edge(node_a, node_b, length=length, maxspeed=speed_kmh, travel_time=travel_time, geometry=geom)
    G.add_edge(node_b, node_a, length=length, maxspeed=speed_kmh, travel_time=travel_time, geometry=geom)

for name, lat1, lon1, lat2, lon2, speed in manual_edges:
    add_manual_connection(G, lat1, lon1, lat2, lon2, speed)

# -----------------------------
# Load cities
# -----------------------------
cities = {}

def load_city_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            cities[data["name"].lower()] = data["location"]

load_city_file(PROJECT_ROOT / "Data" / "Other Data" / "dk_city_data" / "dk" / "place_city.ndjson")
load_city_file(PROJECT_ROOT / "Data" / "Other Data" / "se_city_data" / "se" / "place_city.ndjson")
load_city_file(PROJECT_ROOT / "Data" / "Other Data" / "no_city_data" / "no" / "place_city.ndjson")

# Custom locations
cities.update({
    "arlanda airport": (17.9331197, 59.6523122),
    "kastrup airport": (12.6494168, 55.6296397),
    "gardermoen airport": (11.0967803, 60.1929196),
    "narvik": (17.4432093, 68.4417246)
})

# -----------------------------
# Normalize names
# -----------------------------
def normalize_city_name(name):
    name = name.lower()
    replacements = {"ø": "o", "æ": "ae"}
    for k, v in replacements.items():
        name = name.replace(k, v)
    return ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')

normalized_lookup = {normalize_city_name(c): c for c in cities.keys()}

def get_node_from_name(city):
    norm = normalize_city_name(city)
    if norm in normalized_lookup:
        city_name = normalized_lookup[norm]
        lon, lat = cities[city_name]
        node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
        return city_name, node
    else:
        raise ValueError(f"City not found: {city}")

city_name_origin, origin = get_node_from_name(origin_input)
city_name_dest, destination = get_node_from_name(destination_input)

via_nodes = []
via_names = []
for via in via_inputs:
    if via.strip():
        n, node = get_node_from_name(via)
        via_names.append(n)
        via_nodes.append(node)

# -----------------------------
# Compute route
# -----------------------------
route_nodes = [origin] + via_nodes + [destination]
route = []

for i in range(len(route_nodes)-1):
    segment = nx.shortest_path(G, route_nodes[i], route_nodes[i+1], weight="travel_time")
    if i > 0:
        segment = segment[1:]
    route.extend(segment)

# -----------------------------
# Calculate totals
# -----------------------------
total_distance = 0
total_time = 0
route_lons, route_lats, hover_texts = [], [], []

for u, v in zip(route[:-1], route[1:]):
    data = G.get_edge_data(u, v)[list(G.get_edge_data(u, v).keys())[0]]
    length = data.get("length", 0)
    travel_time = data.get("travel_time", 0)
    geom = data.get("geometry")
    if geom:
        x, y = geom.xy
        for xi, yi in zip(x, y):
            route_lons.append(xi)
            route_lats.append(yi)
            hover_texts.append(None)
        route_lons.append(None)
        route_lats.append(None)
    total_distance += length
    total_time += travel_time

num_stops = 1 + len(via_nodes)
total_time += num_stops * STOP_TIME
total_distance_km = total_distance / 1000
total_time_hours = total_time / 3600

# -----------------------------
# Print summary (GUI output)
# -----------------------------
summary_lines = [
    f"Origin: {city_name_origin.title()}",
    f"Via: {' → '.join([v.title() for v in via_names]) if via_names else 'None'}",
    f"Destination: {city_name_dest.title()}",
    f"Distance: {total_distance_km:.2f} km",
    f"Travel time: {total_time_hours:.2f} hours",
    f"Includes dwell time: {num_stops*3} minutes"
]

print("\n----- ROUTE SUMMARY -----")
print("\n".join(summary_lines))
print("--------------------------\n")

# -----------------------------
# Plot map
# -----------------------------
fig = go.Figure()

# Rail lines by speed
for speed in sorted(edges["maxspeed"].dropna().unique()):
    subset = edges[edges["maxspeed"] == speed]
    lons, lats = [], []
    for geom in subset.geometry:
        if geom:
            x, y = geom.xy
            lons.extend(x)
            lats.extend(y)
            lons.append(None)
            lats.append(None)
    fig.add_trace(go.Scattermap(lon=lons, lat=lats, mode="lines", line=dict(width=1), name=f"{int(speed)} km/h"))

# Fastest route in red
fig.add_trace(go.Scattermap(
    lon=route_lons, lat=route_lats, mode="lines", line=dict(width=4, color="red"),
    name="Fastest route", hoverinfo="text", text=[f"{total_distance_km:.1f} km, {total_time_hours:.1f} h"]
))

# Cities
fig.add_trace(go.Scattermap(
    lon=[c[0] for c in cities.values()],
    lat=[c[1] for c in cities.values()],
    mode="markers+text",
    marker=dict(size=6, color="blue"),
    text=[n.title() for n in cities.keys()],
    textposition="top right",
    name="Cities"
))

fig.update_layout(
    map_style="carto-positron",
    map_zoom=6,
    map_center={"lat": 57.5, "lon": 13.0},
    height=900,
    margin=dict(r=0, t=0, l=0, b=0)
)

fig.show()
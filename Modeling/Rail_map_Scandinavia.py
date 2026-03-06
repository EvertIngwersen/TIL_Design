# -*- coding: utf-8 -*-
"""
Scandinavia rail network 
- plots edges colored by maxspeed
- finds fastest route between any DK, SE and NO city
- border connections manually added
"""

import json
import numpy as np
import osmnx as ox
import unicodedata
import networkx as nx
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px  

from pathlib import Path
from shapely.geometry import LineString

print("Loading data...")    
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

# Offset Sweden node IDs to avoid collision
max_dk_node = max(G_dk.nodes)
G_se = nx.relabel_nodes(G_se, lambda x: x + max_dk_node + 1)

# Merge graphs
G = nx.compose(G_dk, G_se)

# -----------------------------
# Convert to GeoDataFrames
# -----------------------------
nodes, edges = ox.graph_to_gdfs(G)
edges = edges.to_crs(epsg=4326)

# -----------------------------
# Clean maxspeed
# -----------------------------
if "maxspeed" in edges.columns:
    edges["maxspeed"] = (
        edges["maxspeed"]
        .astype(str)
        .str.extract(r"(\d+)")
        .astype(float)
    )
else:
    edges["maxspeed"] = np.nan

# -----------------------------
# Compute travel time
# -----------------------------
edges["travel_time"] = edges["length"] / (edges["maxspeed"] * (1000/3600))
edges["travel_time"] = edges["travel_time"].replace([np.inf, -np.inf], np.nan)
edges["travel_time"] = edges["travel_time"].fillna(
    edges["length"] / (100 * (1000/3600))
)

G = ox.graph_from_gdfs(nodes, edges)

# Find the current maximum node ID after DK+SE merge
max_node = max(G.nodes)

# Offset Norway node IDs to avoid collision
G_no = nx.relabel_nodes(G_no, lambda x: x + max_node + 1)

# Merge Norway into the main graph
G = nx.compose(G, G_no)

# Re-create GeoDataFrames
nodes, edges = ox.graph_to_gdfs(G)
edges = edges.to_crs(epsg=4326)

# Clean maxspeed again if needed
if "maxspeed" in edges.columns:
    edges["maxspeed"] = (
        edges["maxspeed"]
        .astype(str)
        .str.extract(r"(\d+)")
        .astype(float)
    )
else:
    edges["maxspeed"] = np.nan

# Compute travel time
edges["travel_time"] = edges["length"] / (edges["maxspeed"] * (1000/3600))
edges["travel_time"] = edges["travel_time"].replace([np.inf, -np.inf], np.nan)
edges["travel_time"] = edges["travel_time"].fillna(
    edges["length"] / (100 * (1000/3600))  # fallback 100 km/h
)

# Rebuild graph with updated edges
G = ox.graph_from_gdfs(nodes, edges)

# ---------------------------------------------------
#  ADD ØRESUND BRIDGE CONNECTION (200 km/h)
# ---------------------------------------------------

# Coordinates:
# Coord of end of rail piece - Denmark side
cph_lat, cph_lon = 55.5990688, 12.7514874

# Coord of end of rail piece - Sweden / Malmo side
malmo_lat, malmo_lon = 55.5655404, 12.9042758

node_cph = ox.distance.nearest_nodes(G, X=cph_lon, Y=cph_lat)
node_malmo = ox.distance.nearest_nodes(G, X=malmo_lon, Y=malmo_lat)

# Compute bridge length (meters)
bridge_length = ox.distance.great_circle(
    cph_lat, cph_lon,
    malmo_lat, malmo_lon
)

bridge_speed = 200  # km/h
bridge_travel_time = bridge_length / (bridge_speed * (1000/3600))

# Add bidirectional edge
bridge_geom = LineString([
    (cph_lon, cph_lat),
    (malmo_lon, malmo_lat)
])

G.add_edge(node_cph, node_malmo,
           length=bridge_length,
           maxspeed=bridge_speed,
           travel_time=bridge_travel_time,
           geometry=bridge_geom)

G.add_edge(node_malmo, node_cph,
           length=bridge_length,
           maxspeed=bridge_speed,
           travel_time=bridge_travel_time,
           geometry=bridge_geom)

nodes, edges = ox.graph_to_gdfs(G)
edges = edges.to_crs(epsg=4326)

print("Øresund bridge connection added.")

# ---------------------------------------------------
#  ADD SKOTTESJON - ED BORDER CROSSING [NO-SE]
# ---------------------------------------------------

# Coordinates 
# Coordinates end rail piece Norway-Side (SKOTTESJON)
Skottesjon_lat, Skottesjon_lon = 58.9188632, 11.7195089 

# Coordinates end rail piece Sweden-Side (ED)
Ed_lat, Ed_lon = 58.9128502, 11.9275408

node_skottersjon = ox.distance.nearest_nodes(G, X=Skottesjon_lon, Y=Skottesjon_lat)
node_ed = ox.distance.nearest_nodes(G, X=Ed_lon, Y=Ed_lat)

# Compute edge length (meters)
ED_SKOTTERSJON_edge_length = ox.distance.great_circle(
    Skottesjon_lat, Skottesjon_lon,
    Ed_lat, Ed_lon
)

ED_SKOTTERSJON_edge_speed = 120  # km/h
ED_SKOTTERSJON_edge_time = ED_SKOTTERSJON_edge_length / (ED_SKOTTERSJON_edge_speed * (1000/3600))

# Add bidirectional edge
ED_SKOTTERSJON_edge_geom = LineString([
    (Skottesjon_lon, Skottesjon_lat),
    (Ed_lon, Ed_lat)
])

G.add_edge(node_skottersjon, node_ed,
           length=ED_SKOTTERSJON_edge_length,
           maxspeed=ED_SKOTTERSJON_edge_speed,
           travel_time=ED_SKOTTERSJON_edge_time,
           geometry=ED_SKOTTERSJON_edge_geom)

G.add_edge(node_ed, node_skottersjon,
           length=ED_SKOTTERSJON_edge_length,
           maxspeed=ED_SKOTTERSJON_edge_speed,
           travel_time=ED_SKOTTERSJON_edge_time,
           geometry=ED_SKOTTERSJON_edge_geom)

nodes, edges = ox.graph_to_gdfs(G)
edges = edges.to_crs(epsg=4326)


print("Skottesjön - Ed border connection added.")

# ---------------------------------------------------
#  ADD GLASBRUK - CHARLOTTENBERG BORDER CROSSING [NO-SE]
# ---------------------------------------------------

# Coordinates 
# Coordinates end rail piece Norway-Side (SKOTTESJON)
Glasbruk_lat, Glasbruk_lon = 59.9135771, 12.2852937

# Coordinates end rail piece Sweden-Side (ED)
Charlot_lat, Charlot_lon = 59.887603, 12.2936895

node_glasbruk = ox.distance.nearest_nodes(G, X=Glasbruk_lon, Y=Glasbruk_lat)
node_charlot = ox.distance.nearest_nodes(G, X=Charlot_lon, Y=Charlot_lat)

# Compute edge length (meters)
GLASBURK_CHARLOT_edge_length = ox.distance.great_circle(
    Charlot_lat, Charlot_lon,
    Glasbruk_lat, Glasbruk_lon
)

GLASBURK_CHARLOT_edge_speed = 160  # km/h
GLASBURK_CHARLOT_edge_time = GLASBURK_CHARLOT_edge_length / (GLASBURK_CHARLOT_edge_speed * (1000/3600))

# Add bidirectional edge
GLASBURK_CHARLOT_edge_geom = LineString([
    (Charlot_lon, Charlot_lat),
    (Glasbruk_lon, Glasbruk_lat)
])

G.add_edge(node_glasbruk, node_charlot,
           length=GLASBURK_CHARLOT_edge_length,
           maxspeed=GLASBURK_CHARLOT_edge_speed,
           travel_time=GLASBURK_CHARLOT_edge_time,
           geometry=GLASBURK_CHARLOT_edge_geom)

G.add_edge(node_charlot, node_glasbruk, 
           length=GLASBURK_CHARLOT_edge_length,
           maxspeed=GLASBURK_CHARLOT_edge_speed,
           travel_time=GLASBURK_CHARLOT_edge_time,
           geometry=GLASBURK_CHARLOT_edge_geom)

nodes, edges = ox.graph_to_gdfs(G)
edges = edges.to_crs(epsg=4326)


print("Glasbruk - Charolletenberg border connection added.")

# ---------------------------------------------------
#  ADD TEVALDEN - STORLIEN BORDER CROSSING [NO-SE]
# ---------------------------------------------------

# Coordinates 
# Coordinates end rail piece Norway-Side (TEVALDEN)
Tevalden_lat, Tevalden_lon = 63.3264157, 12.0628143

# Coordinates end rail piece Sweden-Side (STORLIEN)
Storlien_lat, Storlien_lon = 63.3172724, 12.0947319

node_tevalden = ox.distance.nearest_nodes(G, X=Tevalden_lon, Y=Tevalden_lat)
node_storlien = ox.distance.nearest_nodes(G, X=Storlien_lon, Y=Storlien_lat)

# Compute edge length (meters)
TEVALDEN_STORLIEN_edge_length = ox.distance.great_circle(
    Storlien_lat, Storlien_lon,
    Tevalden_lat, Tevalden_lon)

TEVALDEN_STORLIEN_edge_speed = 80  # km/h
TEVALDEN_STORLIEN_edge_time = TEVALDEN_STORLIEN_edge_length / (TEVALDEN_STORLIEN_edge_speed * (1000/3600))

# Add bidirectional edge
TEVALDEN_STORLIEN_edge_geom = LineString([
    (Storlien_lon, Storlien_lat),
    (Tevalden_lon, Tevalden_lat)
])


G.add_edge(node_tevalden, node_storlien,
           length=TEVALDEN_STORLIEN_edge_length,
           maxspeed=TEVALDEN_STORLIEN_edge_speed,
           travel_time=TEVALDEN_STORLIEN_edge_time,
           geometry=TEVALDEN_STORLIEN_edge_geom)

G.add_edge(node_storlien, node_tevalden,
           length=TEVALDEN_STORLIEN_edge_length,
           maxspeed=TEVALDEN_STORLIEN_edge_speed,
           travel_time=TEVALDEN_STORLIEN_edge_time,
           geometry=TEVALDEN_STORLIEN_edge_geom)

nodes, edges = ox.graph_to_gdfs(G)
edges = edges.to_crs(epsg=4326)


print("Tevalden - Storlien border connection added.")

# ---------------------------------------------------
#  ADD HELL - STJORDAL CONNECTION [NO]
# ---------------------------------------------------

# Coordinates 
# Coordinates end rail piece (HELL)
Hell_lat, Hell_lon = 63.4462156, 10.9000683  

# Coordinates end rail piece (STJORDAL)
Stjordal_lat, Stjordal_lon = 63.4460545, 10.9063916

node_hell = ox.distance.nearest_nodes(G, X=Hell_lon, Y=Hell_lat)
node_stjordal = ox.distance.nearest_nodes(G, X=Stjordal_lon, Y=Stjordal_lat)

# Compute edge length (meters)
HELL_STJORDAL_edge_length = ox.distance.great_circle(
    Hell_lat, Hell_lon,
    Stjordal_lat, Stjordal_lon
)

HELL_STJORDAL_edge_speed = 60  # km/h  
HELL_STJORDAL_edge_time = HELL_STJORDAL_edge_length / (HELL_STJORDAL_edge_speed * (1000/3600))

# Add bidirectional edge
HELL_STJORDAL_edge_geom = LineString([
    (Hell_lon, Hell_lat),
    (Stjordal_lon, Stjordal_lat)
])

G.add_edge(node_hell, node_stjordal,
           length=HELL_STJORDAL_edge_length,
           maxspeed=HELL_STJORDAL_edge_speed,
           travel_time=HELL_STJORDAL_edge_time,
           geometry=HELL_STJORDAL_edge_geom)

G.add_edge(node_stjordal, node_hell,
           length=HELL_STJORDAL_edge_length,
           maxspeed=HELL_STJORDAL_edge_speed,
           travel_time=HELL_STJORDAL_edge_time,
           geometry=HELL_STJORDAL_edge_geom)

nodes, edges = ox.graph_to_gdfs(G)
edges = edges.to_crs(epsg=4326)

print("Hell - Stjordal connection added.")

# ---------------------------------------------------
#  ADD KOLSAN - NES CONNECTION [NO]
# ---------------------------------------------------

# Coordinates
# Coordinates end rail piece (KOLSAN)
Kolsan_lat, Kolsan_lon = 63.6527907, 11.0889117

# Coordinates end rail piece (NES)
Nes_lat, Nes_lon = 63.6538856, 11.0923136

node_kolsan = ox.distance.nearest_nodes(G, X=Kolsan_lon, Y=Kolsan_lat)
node_nes = ox.distance.nearest_nodes(G, X=Nes_lon, Y=Nes_lat)

# Compute edge length (meters)
KOLSAN_NES_edge_length = ox.distance.great_circle(
    Kolsan_lat, Kolsan_lon,
    Nes_lat, Nes_lon
)

KOLSAN_NES_edge_speed = 80  # km/h
KOLSAN_NES_edge_time = KOLSAN_NES_edge_length / (KOLSAN_NES_edge_speed * (1000/3600))

# Add bidirectional edge
KOLSAN_NES_edge_geom = LineString([
    (Kolsan_lon, Kolsan_lat),
    (Nes_lon, Nes_lat)
])

G.add_edge(node_kolsan, node_nes,
           length=KOLSAN_NES_edge_length,
           maxspeed=KOLSAN_NES_edge_speed,
           travel_time=KOLSAN_NES_edge_time,
           geometry=KOLSAN_NES_edge_geom)

G.add_edge(node_nes, node_kolsan,
           length=KOLSAN_NES_edge_length,
           maxspeed=KOLSAN_NES_edge_speed,
           travel_time=KOLSAN_NES_edge_time,
           geometry=KOLSAN_NES_edge_geom)

nodes, edges = ox.graph_to_gdfs(G)
edges = edges.to_crs(epsg=4326)

print("Kolsan - Nes connection added.")

# -----------------------------
# Load city databases
# -----------------------------
cities = {}

# Denmark
dk_city_file = PROJECT_ROOT / "Data" / "Other Data" / "dk_city_data" / "dk" / "place_city.ndjson"
with open(dk_city_file, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        cities[data["name"].lower()] = data["location"]

# Sweden
se_city_file = PROJECT_ROOT / "Data" / "Other Data" / "se_city_data" / "se" / "place_city.ndjson"
with open(se_city_file, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        cities[data["name"].lower()] = data["location"]

# Norway
no_city_file = PROJECT_ROOT / "Data" / "Other Data" / "no_city_data" / "no" / "place_city.ndjson"
with open(no_city_file, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        cities[data["name"].lower()] = data["location"]



# -----------------------------
# Add custom locations (airports, points of interest)
# -----------------------------
cities["arlanda airport"] = (17.9331197, 59.6523122)  # (lon, lat)
cities["kastrup airport"] = (12.6494168, 55.6296397)
cities["gardermoen airport"] = (11.0967803, 60.1929196)


# ----------------------------------------
# Ask user input
# -------------------------------------------

def normalize_city_name(name):
    """
    Convert letters like å, ä, ö to a, a, o for easier typing.
    """
    name = name.lower()
    name_norm = unicodedata.normalize('NFD', name)
    name_ascii = ''.join(c for c in name_norm if unicodedata.category(c) != 'Mn')
    return name_ascii


# Create a lookup dictionary from normalized names to original names
normalized_lookup = {}
for city in cities.keys():
    normalized_name = normalize_city_name(city)
    normalized_lookup[normalized_name] = city 

def get_city_node(prompt):
    while True:
        user_input = input(prompt).strip().lower()
        normalized_input = normalize_city_name(user_input)
        if normalized_input in normalized_lookup:
            city_name = normalized_lookup[normalized_input]
            if city_name != user_input:
                print(f"Interpreted '{user_input}' as '{city_name.title()}'")
            lon, lat = cities[city_name]
            node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
            return city_name, node
        else:
            print("City not found. Try again.")


print("Available cities:", ", ".join(list(cities.keys())))
print("")
print("Available airports: arlanda airport, kastrup airport, gardermoen airport")
city_name_1, origin = get_city_node("Enter origin city: ")
city_name_2, destination = get_city_node("Enter destination city: ")

print("")
print("Calulating shortest route...")

route = nx.shortest_path(G, origin, destination, weight="travel_time")

# -----------------------------
# Calculate cumulative distance & travel time for hover
# -----------------------------
total_distance = 0  # meters
total_time = 0      # seconds

route_lons = []
route_lats = []
hover_texts = []

for u, v in zip(route[:-1], route[1:]):
    edge_data = G.get_edge_data(u, v)
    first_key = list(edge_data.keys())[0]
    data = edge_data[first_key]

    length = data.get("length", 0)           # meters
    travel_time = data.get("travel_time", 0) # seconds

    geom = data.get("geometry")
    if geom:
        x, y = geom.xy
        for xi, yi in zip(x, y):
            route_lons.append(xi)
            route_lats.append(yi)
            # Append cumulative info at each point
            hover_texts.append(
                f"Cumulative distance: {total_distance/1000:.2f} km\n"
                f"Cumulative time: {total_time/3600:.2f} h"
            )
        # After each edge, add its distance/time to totals
        total_distance += length
        total_time += travel_time
        # Add a None separator for Plotly
        route_lons.append(None)
        route_lats.append(None)
        hover_texts.append(None)

# Convert totals
total_distance_km = total_distance / 1000
total_time_hours = total_time / 3600

print("Shortes route calculated!")
print("")
print("\n----- ROUTE SUMMARY -----")
print(f"Origin: {city_name_1.title()}")
print(f"Destination: {city_name_2.title()}")
print(f"Distance: {total_distance_km:.2f} km")
print(f"Travel time: {total_time_hours:.2f} hours")
print("--------------------------\n")
print("")
print("Creating map...")

# -----------------------------
# Total route info for hover
# -----------------------------
route_hover_text = (
    f"Origin: {city_name_1.title()}\n"
    f"Destination: {city_name_2.title()}\n"
    f"Distance: {total_distance_km:.2f} km\n"
    f"Travel time: {total_time_hours:.2f} hours"
)

# -----------------------------
# Plot
# -----------------------------
fig = go.Figure()

# Plot rail lines by speed
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
        line=dict(width=1),
        name=f"{int(speed)} km/h"
    ))

# Route in red
fig.add_trace(go.Scattermap(
    lon=route_lons,
    lat=route_lats,
    mode="lines",
    line=dict(width=4, color="red"),
    name="Fastest route",
    hoverinfo="text",
    text=[route_hover_text]  
))

# -----------------------------
# Add cities
# -----------------------------
city_lons = []
city_lats = []
city_names = []

for name, (lon, lat) in cities.items():
    city_lons.append(lon)
    city_lats.append(lat)
    city_names.append(name.title())

fig.add_trace(go.Scattermap(
    lon=city_lons,
    lat=city_lats,
    mode="markers+text",
    marker=dict(size=6, color="blue"),
    text=city_names,
    textposition="top right",
    name="Cities",
    hoverinfo="text"
))

# -----------------------------
# Final layout
# -----------------------------
fig.update_layout(
    map_style="carto-positron",
    map_zoom=6,
    map_center={"lat": 57.5, "lon": 13.0},
    height=900,
    margin=dict(r=0, t=0, l=0, b=0)
)

fig.show()
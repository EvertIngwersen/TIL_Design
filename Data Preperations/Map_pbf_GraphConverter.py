# -*- coding: utf-8 -*-
"""
Create Norway railway GraphML with maxspeed attribute
"""

import os
import osmnx as ox
import time

print("OSMnx version:", ox.__version__)

# -------------------------------------------------------
# Get script directory
# -------------------------------------------------------

current_dir = os.path.dirname(__file__)

# -------------------------------------------------------
# Build relative path to OSM file
# -------------------------------------------------------

osm_path = os.path.join(
    current_dir,
    "..",
    "Data",
    "Other Data",
    "norway-260303.osm_01.osm"
)

osm_path = os.path.abspath(osm_path)

# -------------------------------------------------------
# Build save path
# -------------------------------------------------------

save_path = os.path.join(
    current_dir,
    "..",
    "Data",
    "Rail Data",
    "Norway_rail.graphml"
)

save_path = os.path.abspath(save_path)

print("\nLoading OSM file...")
print("OSM path:", osm_path)

start = time.time()

# -------------------------------------------------------
# Load full XML
# -------------------------------------------------------

G = ox.graph_from_xml(
    osm_path,
    simplify=True,
    retain_all=True,
    bidirectional=True
)

print("Loaded full graph.")
print("Time:", round(time.time() - start, 2), "seconds")

# -------------------------------------------------------
# Convert to GeoDataFrames
# -------------------------------------------------------

print("\nFiltering railway=rail...")

nodes, edges = ox.graph_to_gdfs(G)

# Keep only railway tracks
edges = edges[edges["railway"] == "rail"]

# Keep only relevant columns (optional but clean)
keep_cols = [
    "geometry",
    "length",
    "railway",
    "maxspeed"
]

edges = edges[[col for col in keep_cols if col in edges.columns]]

# Rebuild graph
G_rail = ox.graph_from_gdfs(nodes, edges)

print("Rail graph created.")
print("Nodes:", len(G_rail.nodes))
print("Edges:", len(G_rail.edges))

# -------------------------------------------------------
# Save GraphML
# -------------------------------------------------------

print("\nSaving GraphML...")

ox.save_graphml(G_rail, save_path)

print("Saved successfully to:")
print(save_path)
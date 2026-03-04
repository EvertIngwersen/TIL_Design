"""
Download entire Norway rail network including maxspeed
(Single-country download)
"""

import osmnx as ox
import networkx as nx
import pandas as pd
import logging
import time

# -------------------------------------------------------
# OSMnx settings for large downloads
# -------------------------------------------------------

ox.settings.use_cache = True
ox.settings.log_console = True
ox.settings.log_file = True  # <- enables detailed logging
ox.settings.timeout = 600

logging.basicConfig(level=logging.INFO)

# -------------------------------------------------------
# Download Norway rail network
# -------------------------------------------------------

print("Downloading Norway rail network...")

start_time = time.time()

G = ox.graph_from_place(
    "Norway",
    custom_filter='["railway"="rail"]',
    simplify=True,
    retain_all=True
)

duration = round(time.time() - start_time, 1)
print(f"Download complete in {duration} seconds")
print("Nodes:", len(G.nodes))
print("Edges:", len(G.edges))
print(type(G))

# -------------------------------------------------------
# Convert to GeoDataFrames
# -------------------------------------------------------

nodes, edges = ox.graph_to_gdfs(G)

print("\nEdge columns:")
print(edges.columns)
print(edges.head())

# -------------------------------------------------------
# Clean maxspeed column (if present)
# -------------------------------------------------------

if "maxspeed" in edges.columns:
    edges["maxspeed"] = (
        edges["maxspeed"]
        .astype(str)
        .str.extract(r"(\d+)")
        .astype(float)
    )

    print("\nMaxspeed summary:")
    print(edges["maxspeed"].describe())

    print(
        "Percentage with speed data:",
        round(edges["maxspeed"].notna().mean() * 100, 2),
        "%"
    )
else:
    print("\nNo maxspeed tag found in OSM data.")

# -------------------------------------------------------
# Save graph
# -------------------------------------------------------

ox.save_graphml(G, "Norway_rail.graphml")
ox.save_graph_geopackage(G, "Norway_rail.gpkg")

print("\nNorway rail network saved.")
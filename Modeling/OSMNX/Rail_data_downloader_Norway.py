# -*- coding: utf-8 -*-

"""
Download entire Norway rail network including maxspeed
(Fast bounding-box version – stable for large countries)
"""

import osmnx as ox
import networkx as nx
import pandas as pd
import logging
import time

# -------------------------------------------------------
# -------------------------------------------------------
# OSMnx settings for large downloads
# -------------------------------------------------------

ox.settings.use_cache = True
ox.settings.log_console = True
ox.settings.log_file = True

# Allow very large queries (prevents thousands of tiles)
ox.settings.max_query_area_size = 5e11  # 500 billion m²

# Increase server timeout
ox.settings.timeout = 600

# Increase Overpass memory allowance
ox.settings.overpass_settings = '[out:json][timeout:600][maxsize:2147483648]'

logging.basicConfig(level=logging.INFO)

# -------------------------------------------------------
# Norway bounding box (much faster than polygon clipping)
# -------------------------------------------------------
# Approximate national bounding box
north = 71.5
south = 57.8
east = 31.5
west = 4.0

# -------------------------------------------------------
# Download Norway rail network
# -------------------------------------------------------

print("\nDownloading Norway rail network (place method)...")

start_time = time.time()

G = ox.graph_from_place(
    "Norway",
    custom_filter='["railway"="rail"]',
    simplify=True,
    retain_all=True
)

duration = round(time.time() - start_time, 1)

print("\nDownload complete")
print(f"Time: {duration} seconds")
print("Nodes:", len(G.nodes))
print("Edges:", len(G.edges))

# -------------------------------------------------------
# Convert to GeoDataFrames
# -------------------------------------------------------

print("\nConverting graph to GeoDataFrames...")
nodes, edges = ox.graph_to_gdfs(G)

print("\nEdge columns:")
print(edges.columns)

# -------------------------------------------------------
# Clean maxspeed column (if present)
# -------------------------------------------------------

if "maxspeed" in edges.columns:
    print("\nCleaning maxspeed column...")

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

print("\nSaving files...")

ox.save_graphml(G, "Norway_rail.graphml")
ox.save_graph_geopackage(G, "Norway_rail.gpkg")

print("\nNorway rail network saved successfully.")
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 17 12:10:31 2026

@author: evert
"""

import numpy as np
import osmnx as ox
import networkx as nx
import plotly.graph_objects as go
import plotly.io as pio
import random

pio.renderers.default = "browser"

G = ox.load_graphml("Sweden_rail.graphml")
ox.save_graph_geopackage(G, "Sweden_rail.gpkg")

print("Nodes:", len(G.nodes))
print("Edges:", len(G.edges))
print(type(G))
ox.plot_graph(G)
nodes, edges = ox.graph_to_gdfs(G)



# Ensure WGS84
edges = edges.to_crs(epsg=4326)

# Create coordinate arrays (single trace!)
lons = []
lats = []

for geom in edges.geometry:
    if geom is not None:
        x, y = geom.xy
        lons.extend(x)
        lats.extend(y)
        lons.append(None)  # break between segments
        lats.append(None)

fig = go.Figure(
    go.Scattermap(
        lon=lons,
        lat=lats,
        mode="lines",
        line=dict(width=1),
        hoverinfo="skip"
    )
)

fig.update_layout(
    map_style="carto-positron",
    map_zoom=5,
    map_center={"lat": 62, "lon": 15},
    height=900,
    margin=dict(r=0, t=0, l=0, b=0)
)

fig.show()








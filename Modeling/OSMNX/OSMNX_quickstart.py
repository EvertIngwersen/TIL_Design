# -*- coding: utf-8 -*-
"""
Created on Mon Feb 16 13:03:35 2026

@author: evert
"""

import osmnx as ox
import networkx as nx


G = ox.graph_from_place(
    "Sweden",
    custom_filter='["railway"~"rail"]',
    simplify=True,       # merge intermediate nodes
    retain_all=False     # only largest component (optional)
)

ox.plot_graph(G)

nodes, edges = ox.graph_to_gdfs(G)
print(nodes.head())
print(edges.head())

ox.save_graphml(G, "Sweden_rail.graphml")



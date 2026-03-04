# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 11:29:11 2026

@author: evert
"""

import os
import osmnx as ox

# paths
current_dir = os.path.dirname(__file__)
osm_file = os.path.abspath(os.path.join(current_dir, "..", "Data", "Other Data", "norway-rail.osm"))
save_file = os.path.abspath(os.path.join(current_dir, "..", "Data", "Rail Data", "Norway_rail.graphml"))

# load graph (already filtered for railways in osmfilter)
G = ox.graph_from_xml(osm_file, retain_all=True)

# save
ox.save_graphml(G, save_file)

print("Graph saved successfully.")
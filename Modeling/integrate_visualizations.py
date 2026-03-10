# -*- coding: utf-8 -*-
"""
Integration script showing how to use the visualization module
with your existing air-rail synchronization model.

Add this at the end of your main model file.
"""

from visualization_module import visualize_solution

# After your model has been solved (after M3 optimization):
# ==========================================================
# GENERATE VISUALIZATIONS
# ==========================================================

print("\n" + "="*70)
print("GENERATING VISUALIZATIONS")
print("="*70)

# Prepare parameters dictionary for visualizer
visualization_params = {
    'I': I,
    'I_T': I_T,
    'K_out': K_out,
    'K_in': K_in,
    'S_i': S_i,
    'ori_i': ori_i,
    'des_i': des_i,
    'D_k': D_k,
    'A_m': A_m,
    'demand_out': demand_out,
    'demand_in': demand_in,
    'flight_station_out': flight_station_out,
    'flight_station_in': flight_station_in,
    'station_coords': station_coords,
    'l_k': l_k,
    'u_k': u_k,
    'l_m': l_m,
    'u_m': u_m
}

# Generate all visualizations and save as HTML
figures = visualize_solution(
    model=model,
    parameters=visualization_params,
    save_html=True,
    output_dir='visualizations'
)

# Show individual visualizations in browser
print("\nOpening visualizations in browser...")

# 1. Show Gantt Chart
figures['gantt'].show()

# 2. Show Synchronization Network
figures['network'].show()

# 3. Show Demand Coverage Analysis
figures['demand'].show()

# 4. Show Quality Metrics Dashboard
figures['metrics'].show()

# 5. Show Time-Space Diagram
figures['timespace'].show()

print("\n" + "="*70)
print("All visualizations have been generated and saved!")
print("Check the 'visualizations' folder for HTML files.")
print("="*70)

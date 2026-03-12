#
# ==========================================================
# VISUALIZATION QUICK REFERENCE GUIDE
# ==========================================================
"""
This guide explains all available visualizations for your
Air-Rail Synchronization Optimization model.

SETUP:
------
1. Copy these files to your project directory:
   - visualization_module.py
   - advanced_demand_visualization.py
   - complete_visualization_example.py

2. At the end of your model file, add:
   exec(open('complete_visualization_example.py').read())

3. Run your model - visualizations will be generated automatically!

==========================================================
AVAILABLE VISUALIZATIONS (9 total)
==========================================================

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 STANDARD VISUALIZATIONS (5 charts)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. GANTT CHART
   Purpose: Visualize train schedules and flight timing
   Shows:
   - Train journeys as horizontal bars
   - Flight departure/arrival windows
   - Synchronization connections
   - Color coding by productivity
   Use for: Understanding temporal structure of solution

2. SYNCHRONIZATION NETWORK
   Purpose: Show train-flight connections by station
   Shows:
   - Trains (blue squares) on the left
   - Outgoing flights (orange triangles up)
   - Incoming flights (green triangles down)
   - Connection lines between synchronized pairs
   Use for: Understanding connection topology at each airport

3. DEMAND COVERAGE ANALYSIS (4 subplots)
   Purpose: Comprehensive demand analysis dashboard
   Subplot 3a: Outgoing flight demand (covered vs uncovered)
   Subplot 3b: Incoming flight demand (covered vs uncovered)
   Subplot 3c: Coverage percentage by time of day
   Subplot 3d: Cumulative passenger coverage over time
   Use for: Evaluating demand satisfaction over time

4. QUALITY METRICS DASHBOARD (6 subplots)
   Purpose: Key performance indicators
   Subplot 4a: Total synchronization count (KPI gauge)
   Subplot 4b: Overall coverage rate (gauge 0-100%)
   Subplot 4c: Transfer time distribution (histogram)
   Subplot 4d: Penalty distribution (box plot)
   Subplot 4e: Station-wise performance (bar chart)
   Subplot 4f: Train utilization (top 15 trains)
   Use for: Quick assessment of solution quality

5. TIME-SPACE DIAGRAM
   Purpose: Classic railway visualization
   Shows:
   - Train trajectories in time-space
   - Station positions on y-axis
   - Time progression on x-axis
   - Line color indicates productivity
   Use for: Identifying conflicts and inefficiencies

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 ADVANCED DEMAND VISUALIZATIONS (4 charts)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6. DEMAND HEATMAP (3 subplots)
   Purpose: Spatial-temporal demand analysis
   Subplot 6a: Total demand by station and hour
   Subplot 6b: Served demand by station and hour
   Subplot 6c: Coverage rate (%) by station and hour
   Use for: Identifying demand hotspots and gaps

7. FLIGHT RANKING CHART
   Purpose: Prioritize high-demand flights
   Shows:
   - Top 30 flights ranked by passenger demand
   - Covered flights (green) vs uncovered (red)
   - Number of connections displayed on bars
   Use for: Understanding which high-value flights are served

8. TRAIN PRODUCTIVITY CHART
   Purpose: Evaluate train utilization
   Shows:
   - Passengers served per train (bars)
   - Number of synchronizations (line)
   - Sorted by productivity
   Use for: Identifying underutilized trains

9. CONNECTION QUALITY SCATTER PLOT
   Purpose: Analyze transfer time vs passenger experience
   Shows:
   - Each connection as a point
   - X-axis: Transfer time (min)
   - Y-axis: Passenger penalty
   - Marker size: Passenger demand
   - Quality zones (optimal, acceptable, poor)
   Use for: Fine-tuning transfer time windows

==========================================================
HOW TO USE SPECIFIC VISUALIZATIONS
==========================================================

OPTION A: Generate all visualizations at once
----------------------------------------------
# At the end of your model file:
from complete_visualization_example import *

# This will:
# - Generate all 9 visualizations
# - Save as HTML files in 'visualizations/' folder
# - Display them in your browser
# - Print a comprehensive summary


OPTION B: Generate only standard visualizations
------------------------------------------------
from visualization_module import visualize_solution

viz_params = {
    'I': I, 'I_T': I_T, 'K_out': K_out, 'K_in': K_in,
    'S_i': S_i, 'ori_i': ori_i, 'des_i': des_i,
    'D_k': D_k, 'A_m': A_m,
    'demand_out': demand_out, 'demand_in': demand_in,
    'flight_station_out': flight_station_out,
    'flight_station_in': flight_station_in,
    'station_coords': station_coords,
    'l_k': l_k, 'u_k': u_k, 'l_m': l_m, 'u_m': u_m
}

figures = visualize_solution(model, viz_params, save_html=True)

# Show specific charts:
figures['gantt'].show()      # Gantt chart
figures['network'].show()    # Network
figures['demand'].show()     # Demand analysis
figures['metrics'].show()    # Quality metrics
figures['timespace'].show()  # Time-space diagram


OPTION C: Generate only demand visualizations
----------------------------------------------
from advanced_demand_visualization import generate_demand_visualizations

demand_figs = generate_demand_visualizations(model, viz_params, save_html=True)

# Show specific charts:
demand_figs['heatmap'].show()       # Demand heatmap
demand_figs['ranking'].show()       # Flight ranking
demand_figs['productivity'].show()  # Train productivity
demand_figs['quality'].show()       # Connection quality


OPTION D: Generate individual visualizations
---------------------------------------------
from visualization_module import AirRailVisualizer

# Extract solution data from model
solution_data = {}  # (see complete_visualization_example.py for extraction code)

# Create visualizer
viz = AirRailVisualizer(solution_data, viz_params)

# Generate individual charts:
fig1 = viz.create_gantt_chart()
fig2 = viz.create_synchronization_network()
fig3 = viz.create_demand_coverage_analysis()
fig4 = viz.create_quality_metrics_dashboard()
fig5 = viz.create_time_space_diagram()

# Show or save:
fig1.show()
fig1.write_html("my_gantt.html")

==========================================================
CUSTOMIZATION OPTIONS
==========================================================

1. Change output directory:
   visualize_solution(model, params, output_dir='my_folder')

2. Don't save HTML (only display):
   visualize_solution(model, params, save_html=False)

3. Customize Gantt chart:
   viz.create_gantt_chart(show_flights=True, show_connections=True)

4. Save as static image (requires kaleido):
   fig.write_image("gantt.png", width=1920, height=1080)

==========================================================
INTERPRETING THE VISUALIZATIONS
==========================================================

🟢 GOOD SIGNS:
- High coverage rate (>80%) in quality metrics
- Transfer times clustered around 45 minutes
- Low penalties (<10) in scatter plot
- Uniform demand coverage across time periods
- Most trains serve multiple connections

🟡 WARNING SIGNS:
- Coverage gaps during peak hours (heatmap)
- High penalties (>20) for many connections
- Transfer times at extremes (20min or 70min)
- Many uncovered high-demand flights (ranking chart)
- Uneven station performance

🔴 ISSUES TO ADDRESS:
- Coverage rate <50%
- Large gaps in heatmap (no service for hours)
- Many trains with zero connections
- Penalties consistently >30

==========================================================
TROUBLESHOOTING
==========================================================

Problem: "Module not found"
Solution: Ensure all .py files are in the same directory

Problem: Blank visualizations
Solution: Check that model has been solved (model.Status == GRB.OPTIMAL)

Problem: "No data to plot"
Solution: Verify that synchronizations were found (check P[i,k] values)

Problem: Slow rendering
Solution: Reduce number of trains/flights or use save_html=True
          and open HTML files instead of .show()

Problem: HTML files won't open
Solution: Use absolute path or move to same directory as script

==========================================================
EXPORTING FOR PRESENTATIONS
==========================================================

# High-resolution PNG (requires kaleido):
pip install kaleido

fig.write_image("figure.png", width=1920, height=1080, scale=2)

# PDF:
fig.write_image("figure.pdf", width=1200, height=800)

# Static HTML (smaller file size):
fig.write_html("figure.html", include_plotlyjs='cdn')

==========================================================
TIPS & BEST PRACTICES
==========================================================

1. Always generate all visualizations after solving
2. Save HTML files for later analysis
3. Use heatmap to identify time-of-day patterns
4. Use scatter plot to fine-tune penalty parameters
5. Compare before/after when changing parameters
6. Share HTML files with stakeholders (interactive!)
7. Use time-space diagram for conflict detection
8. Check train productivity to identify redundancies

==========================================================
CONTACT & SUPPORT
==========================================================

For questions about these visualizations:
- Check the code comments in visualization_module.py
- Review the complete_visualization_example.py
- Modify parameters in the viz_params dictionary

Happy optimizing! 🚄✈️
"""

# ==========================================================
# MINIMAL WORKING EXAMPLE
# ==========================================================

if __name__ == "__main__":
    print(__doc__)
    
    print("\n" + "="*60)
    print("MINIMAL WORKING EXAMPLE")
    print("="*60)
    
    print("""
    # At the end of your model file, add just these 2 lines:
    
    from complete_visualization_example import *
    # That's it! All visualizations will be generated automatically.
    
    # Or for more control:
    
    from visualization_module import visualize_solution
    from advanced_demand_visualization import generate_demand_visualizations
    
    viz_params = {
        'I': I, 'I_T': I_T, 'K_out': K_out, 'K_in': K_in,
        'S_i': S_i, 'ori_i': ori_i, 'des_i': des_i,
        'D_k': D_k, 'A_m': A_m,
        'demand_out': demand_out, 'demand_in': demand_in,
        'flight_station_out': flight_station_out,
        'flight_station_in': flight_station_in,
        'station_coords': station_coords,
        'l_k': l_k, 'u_k': u_k, 'l_m': l_m, 'u_m': u_m
    }
    
    # Standard visualizations
    std_figs = visualize_solution(model, viz_params)
    
    # Demand visualizations
    dem_figs = generate_demand_visualizations(model, viz_params)
    
    # Display all
    for name, fig in {**std_figs, **dem_figs}.items():
        fig.show()
    """)

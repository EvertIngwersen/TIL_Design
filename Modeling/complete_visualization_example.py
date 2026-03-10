# -*- coding: utf-8 -*-
"""
COMPLETE VISUALIZATION EXAMPLE
Add this code at the end of your model file to generate all visualizations.
"""

from visualization_module import visualize_solution
from advanced_demand_visualization import generate_demand_visualizations

# ==========================================================
# AFTER YOUR MODEL HAS BEEN SOLVED (after M3)
# ==========================================================

print("\n" + "="*80)
print(" " * 20 + "GENERATING ALL VISUALIZATIONS")
print("="*80)

# Prepare parameters dictionary
viz_params = {
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

# ==========================================================
# PART 1: STANDARD VISUALIZATIONS
# ==========================================================
print("\n" + "="*80)
print("PART 1: GENERATING STANDARD VISUALIZATIONS")
print("="*80)

standard_figures = visualize_solution(
    model=model,
    parameters=viz_params,
    save_html=True,
    output_dir='visualizations'
)

# Show standard visualizations
print("\nDisplaying standard visualizations...")
standard_figures['gantt'].show()          # Gantt chart
standard_figures['network'].show()        # Synchronization network
standard_figures['demand'].show()         # Demand coverage analysis
standard_figures['metrics'].show()        # Quality metrics dashboard
standard_figures['timespace'].show()      # Time-space diagram

# ==========================================================
# PART 2: ADVANCED DEMAND VISUALIZATIONS
# ==========================================================
print("\n" + "="*80)
print("PART 2: GENERATING ADVANCED DEMAND VISUALIZATIONS")
print("="*80)

demand_figures = generate_demand_visualizations(
    model=model,
    parameters=viz_params,
    save_html=True,
    output_dir='visualizations'
)

# Show demand visualizations
print("\nDisplaying demand visualizations...")
demand_figures['heatmap'].show()          # Demand heatmap by station/time
demand_figures['ranking'].show()          # Flight ranking by demand
demand_figures['productivity'].show()     # Train productivity analysis
demand_figures['quality'].show()          # Connection quality scatter

# ==========================================================
# SUMMARY REPORT
# ==========================================================
print("\n" + "="*80)
print("VISUALIZATION SUMMARY")
print("="*80)

print("\n📊 STANDARD VISUALIZATIONS (5 charts):")
print("  1. ✓ Gantt Chart              - Train schedules over time")
print("  2. ✓ Synchronization Network  - Train-flight connections by station")
print("  3. ✓ Demand Coverage Analysis - 4-panel demand dashboard")
print("  4. ✓ Quality Metrics          - 6-panel performance dashboard")
print("  5. ✓ Time-Space Diagram       - Train trajectories")

print("\n📈 DEMAND VISUALIZATIONS (4 charts):")
print("  6. ✓ Demand Heatmap          - Coverage by station and time")
print("  7. ✓ Flight Ranking          - Flights ranked by demand")
print("  8. ✓ Train Productivity      - Passengers served per train")
print("  9. ✓ Connection Quality      - Transfer time vs penalty")

print("\n💾 FILES SAVED TO: './visualizations/'")
print("  • gantt_chart.html")
print("  • synchronization_network.html")
print("  • demand_coverage.html")
print("  • quality_metrics.html")
print("  • time_space_diagram.html")
print("  • demand_heatmap.html")
print("  • flight_ranking.html")
print("  • train_productivity.html")
print("  • connection_quality.html")

print("\n🎯 KEY INSIGHTS:")

# Calculate some key metrics
total_demand = sum(demand_out.values()) + sum(demand_in.values())
total_served_out = sum(demand_out[k] * (1 if C[k].X > 0.5 else 0) for k in K_out)
total_served_in = sum(demand_in[m] * (1 if C_in[m].X > 0.5 else 0) for m in K_in)
total_served = total_served_out + total_served_in
coverage_pct = (total_served / total_demand * 100) if total_demand > 0 else 0

flights_covered = sum(1 for k in K_out if C[k].X > 0.5)
flights_covered += sum(1 for m in K_in if C_in[m].X > 0.5)
total_flights = len(K_out) + len(K_in)

sync_count = sum(1 for i in I_T for k in K_out if P[i,k].X > 0.5)
sync_count += sum(1 for i in I_T for m in K_in if Q[i,m].X > 0.5)

print(f"  • Passenger Coverage: {coverage_pct:.1f}% ({int(total_served):,}/{int(total_demand):,} passengers)")
print(f"  • Flight Coverage: {flights_covered}/{total_flights} flights ({flights_covered/total_flights*100:.1f}%)")
print(f"  • Total Synchronizations: {sync_count}")
print(f"  • Average connections per covered flight: {sync_count/flights_covered:.1f}" if flights_covered > 0 else "  • No flights covered")

# Find best performing station
from collections import defaultdict
station_performance = defaultdict(lambda: {'demand': 0, 'served': 0})

for k in K_out:
    st = flight_station_out[k]
    station_performance[st]['demand'] += demand_out[k]
    if C[k].X > 0.5:
        station_performance[st]['served'] += demand_out[k]

for m in K_in:
    st = flight_station_in[m]
    station_performance[st]['demand'] += demand_in[m]
    if C_in[m].X > 0.5:
        station_performance[st]['served'] += demand_in[m]

best_station = max(station_performance.keys(), 
                   key=lambda s: station_performance[s]['served'] / station_performance[s]['demand'] 
                   if station_performance[s]['demand'] > 0 else 0)
best_coverage = (station_performance[best_station]['served'] / 
                station_performance[best_station]['demand'] * 100) if station_performance[best_station]['demand'] > 0 else 0

print(f"  • Best performing station: Station {best_station} ({best_coverage:.1f}% coverage)")

# Find most productive train
train_passengers = {}
for i in I:
    pax = 0
    for k in K_out:
        if (i, k) in P and P[i,k].X > 0.5:
            pax += demand_out[k]
    for m in K_in:
        if (i, m) in Q and Q[i,m].X > 0.5:
            pax += demand_in[m]
    train_passengers[i] = pax

if train_passengers:
    best_train = max(train_passengers.keys(), key=lambda t: train_passengers[t])
    print(f"  • Most productive train: Train {best_train} ({train_passengers[best_train]:,} passengers)")

print("\n" + "="*80)
print("✅ ALL VISUALIZATIONS GENERATED SUCCESSFULLY!")
print("="*80)
print("\nOpen the HTML files in your browser for interactive exploration.")
print("Tip: Use the browser's zoom and pan tools for detailed analysis.\n")

# -*- coding: utf-8 -*-
"""
Created on Mon Feb 23 12:17:31 2026

@author: evert
"""

import sys
import base64
import numpy as np
import gurobipy as gp
import plotly.io as pio
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import networkx as nx
import plotly.express as px

from pathlib import Path
from collections import defaultdict
from gurobipy import GRB
from parameters import (
    I, beta, gamma, y, dwell_max, dwell_min,
    dw_lower, dw_upper, aw_lower, aw_upper,
    xs, xe, M, HS, HA, l_k, M_prime, u_k,
    v1, v2, w1, w2, M_double, D_k,
    station_coords, x, S, r, K, H,
    S_i, I_T, transfer_stations, flight_station,
    ori_i, des_i
)

pio.renderers.default = "browser"


# Loading train image (used for animation)


# Get current script directory
current_dir = Path(__file__).parent

# Build relative path to image
train_img_path = current_dir.parent / "Data" / "Other Data" / "steam_train.jpg"

# Encode image to base64 (Plotly requires this)
with open(train_img_path, "rb") as f:
    encoded_image = base64.b64encode(f.read()).decode()

image_source = f"data:image/jpg;base64,{encoded_image}"



# ==========================================================
# 4. MODEL
# ==========================================================

model = gp.Model("Air_HSR_Synchronization")

# ==========================================================
# 5. DECISION VARIABLES
# ==========================================================

# Arrival time a_{i,s}
a = {}
for i in I:
    for s in S_i[i]:
        if s != ori_i[i]:
            a[i, s] = model.addVar(lb=0, ub=H, vtype=GRB.CONTINUOUS,
                                   name=f"a_{i}_{s}")

# Departure time d_{i,s}
d = {}
for i in I:
    for s in S_i[i]:
        if s != des_i[i]:
            d[i, s] = model.addVar(lb=0, ub=H, vtype=GRB.CONTINUOUS,
                                   name=f"d_{i}_{s}")

# O_{i,j}^s (departure order binary)
O = {}
for i in I:
    for j in I:
        if i != j:
            for s in S:
                O[i, j, s] = model.addVar(vtype=GRB.BINARY,
                                          name=f"O_{i}_{j}_{s}")

# P_{i,k} synchronization binary
P = {}
for i in I_T:
    for k in K:
        P[i, k] = model.addVar(vtype=GRB.BINARY,
                               name=f"P_{i}_{k}")

# C_k flight synchronized
C = {}
for k in K:
    C[k] = model.addVar(vtype=GRB.BINARY,
                        name=f"C_{k}")

# p_{i,k} penalty variable
p = {}
for i in I_T:
    for k in K:
        p[i, k] = model.addVar(lb=0, vtype=GRB.CONTINUOUS,
                               name=f"p_{i}_{k}")

model.update()

print("Model successfully created with parameters and decision variables.")

# Objective functions

Z1 = gp.quicksum(P[i, k] for i in I_T for k in K)
Z2 = gp.quicksum(C[k] for k in K)
Z3 = gp.quicksum(p[i, k] for i in I_T for k in K)

print("Objective functions successfully added.")

# Constraints

for i in I:
    stations = S_i[i]
    for idx in range(len(stations) - 1):
        s = stations[idx]
        s_next = stations[idx + 1]

        model.addConstr(
            a[i, s_next] - d[i, s] >=
            r[i, s] +
            beta[i, s] * x[i, s] +
            gamma[i, s_next] * x[i, s_next],
            name=f"run_min_{i}_{s}"
        )
        
for i in I:
    stations = S_i[i]
    for idx in range(len(stations) - 1):
        s = stations[idx]
        s_next = stations[idx + 1]

        model.addConstr(
            a[i, s_next] - d[i, s] <=
            r[i, s] +
            beta[i, s] * x[i, s] +
            gamma[i, s_next] * x[i, s_next] +
            y[i, s],
            name=f"run_max_{i}_{s}"
        )

for i in I:
    for s in S_i[i]:
        if s not in [ori_i[i], des_i[i]]:
            model.addConstr(
                d[i, s] - a[i, s] >= dwell_min[i, s] * x[i, s],
                name=f"dwell_min_{i}_{s}"
            )
            
# for i in I:
#     for s in S_i[i]:
#         if s not in [ori_i[i], des_i[i]]:
#             model.addConstr(
#                 d[i, s] - a[i, s] <= dwell_max[i, s] * x[i, s],
#                 name=f"dwell_max_{i}_{s}"
#             )

# Possible fix:
for i in I:
    for s in S_i[i]:
        if s not in [ori_i[i], des_i[i]]:
            model.addConstr(
                d[i, s] - a[i, s] <= dwell_max[i, s] * x[i, s],  # FIXED
                name=f"dwell_max_{i}_{s}"
            )
    

for i in I:
    model.addConstr(
        d[i, ori_i[i]] >= dw_lower[i],
        name=f"dep_window_low_{i}"
    )
    model.addConstr(
        d[i, ori_i[i]] <= dw_upper[i],
        name=f"dep_window_up_{i}"
    )

for i in I:
    model.addConstr(
        a[i, des_i[i]] >= aw_lower[i],
        name=f"arr_window_low_{i}"
    )
    model.addConstr(
        a[i, des_i[i]] <= aw_upper[i],
        name=f"arr_window_up_{i}"
    )

for i in I:
    for j in I:
        if i != j and (i, j) in xs:

            stations_i = S_i[i]
            stations_j = S_i[j]

            common = sorted(list(set(stations_i).intersection(set(stations_j))))

            for idx in range(len(common) - 1):

                s = common[idx]

                # Only if departure variable exists at s
                if s != des_i[i] and s != des_i[j]:

                    # (16)
                    model.addConstr(
                        d[j, s] - d[i, s] + M * (1 - O[i, j, s])
                        >= HS[s],
                        name=f"dep_headway1_{i}_{j}_{s}"
                    )

                    # (17)
                    model.addConstr(
                        d[i, s] - d[j, s] + M * O[i, j, s]
                        >= HS[s],
                        name=f"dep_headway2_{i}_{j}_{s}"
                    )
                    
for i in I:
    for j in I:
        if i != j and (i, j) in xs:

            stations_i = S_i[i]
            stations_j = S_i[j]

            common = sorted(list(set(stations_i).intersection(set(stations_j))))

            for idx in range(len(common) - 1):

                s = common[idx]
                s_next = common[idx + 1]

                # Only if arrival variable exists
                if s_next != ori_i[i] and s_next != ori_i[j]:

                    # (18)
                    model.addConstr(
                        a[j, s_next] - a[i, s_next] + M * (1 - O[i, j, s])
                        >= HA[s_next],
                        name=f"arr_headway1_{i}_{j}_{s}"
                    )

                    # (19)
                    model.addConstr(
                        a[i, s_next] - a[j, s_next] + M * O[i, j, s]
                        >= HA[s_next],
                        name=f"arr_headway2_{i}_{j}_{s}"
                    )


for i in I:
    for j in I:
        if i < j:  # avoid duplicates

            common = set(S_i[i]).intersection(set(S_i[j]))

            for s in common:

                model.addConstr(
                    O[i, j, s] + O[j, i, s] == 1,
                    name=f"ordering_{i}_{j}_{s}"
                )

# Air-rail synchronization constraints for multiple airports
for i in I_T:
    for k in K:
        st_k = flight_station[k]  # get transfer station for flight k
        
        # Train must visit airport AND it cannot be the origin (need arrival variable)
        if st_k in S_i[i] and st_k != ori_i[i]:
            # Lower bound
            model.addConstr(
                a[i, st_k] >= l_k[k] - M_prime * (1 - P[i, k]),
                name=f"sync_low_{i}_{k}"
            )
            # Upper bound
            model.addConstr(
                a[i, st_k] <= u_k[k] + M_prime * (1 - P[i, k]),
                name=f"sync_up_{i}_{k}"
            )
        else:
            # Train cannot synchronize (doesn't visit airport OR it's the origin)
            model.addConstr(
                P[i, k] == 0,
                name=f"sync_invalid_{i}_{k}"
            )


for k in K:
    model.addConstr(
        C[k] <= gp.quicksum(P[i, k] for i in I_T),
        name=f"coverage_{k}"
    )

mid_k = {k: (l_k[k] + u_k[k]) / 2 for k in K}

for i in I_T:
    for k in K:
        st_k = flight_station[k]
        
        # Only create penalty if train arrives at airport (not origin)
        if st_k in S_i[i] and st_k != ori_i[i]:
            model.addConstr(
                p[i, k] >= v1 * w1 * (a[i, st_k] - mid_k[k]) - (1 - P[i, k]) * M_double,
                name=f"penalty_business_{i}_{k}"
            )
            model.addConstr(
                p[i, k] >= v2 * w2 * (mid_k[k] - a[i, st_k]) - (1 - P[i, k]) * M_double,
                name=f"penalty_leisure_{i}_{k}"
            )
        else:
            # No penalty if train doesn't arrive at this airport
            model.addConstr(
                p[i, k] == 0,
                name=f"penalty_zero_{i}_{k}"
            )


# Solving model

print("\n" + "="*70)
print("MODEL M1: Maximizing Synchronizations")
print("="*70)

model.setObjective(Z1, GRB.MAXIMIZE)
model.optimize()

if model.Status != GRB.OPTIMAL:
    print("ERROR: Model M1 failed!")
    sys.exit()

P_star = model.ObjVal
print(f"Optimal P* = {P_star}")

model.addConstr(
    gp.quicksum(P[i, k] for i in I_T for k in K) == P_star,
    name="fix_Z1"
)

print("\n" + "="*70)
print("MODEL M2: Maximizing Coverage")
print("="*70)

model.setObjective(Z2, GRB.MAXIMIZE)
model.optimize()

if model.Status != GRB.OPTIMAL:
    print("ERROR: Model M2 failed!")
    sys.exit()

C_star = model.ObjVal
print(f"Optimal C* = {C_star}")

model.addConstr(
    gp.quicksum(C[k] for k in K) == C_star,
    name="fix_Z2"
)

print("\n" + "="*70)
print("MODEL M3: Minimizing Penalties")
print("="*70)

model.setObjective(Z3, GRB.MINIMIZE)
model.optimize()

if model.Status != GRB.OPTIMAL:
    print("ERROR: Model M3 failed!")
    sys.exit()

print(f"Optimal Penalty = {model.ObjVal:.2f}")

# Display Results
print("\n" + "="*70)
print("FINAL RESULTS")
print("="*70)
print(f"\nZ1 = {P_star}, Z2 = {C_star}, Z3 = {model.ObjVal:.2f}")

print("\nSynchronizations:")
for i in I_T:
    for k in K:
        if P[i, k].X > 0.5:
            st_k = flight_station[k]  # get the transfer station
            print(f"  Train {i} → Flight {k}: arrival={a[i,st_k].X:.1f}, "
                  f"departure={D_k[k]}, transfer={D_k[k]-a[i,st_k].X:.1f}min, "
                  f"penalty={p[i,k].X:.2f}")

print("\nFlight Coverage:")
for k in K:
    covered = "COVERED" if C[k].X > 0.5 else "NOT COVERED"
    trains = [str(i) for i in I_T if P[i, k].X > 0.5]
    print(f"  Flight {k}: {covered} (trains: {', '.join(trains) if trains else 'none'})")

# --- Parameters from your solution ---
trains = I
flights = K
stations = S

# Collect train schedules
train_schedule = {}
for i in I:
    train_schedule[i] = []
    for s in S_i[i]:
        arr = a[i, s].X if (i, s) in a else None
        dep = d[i, s].X if (i, s) in d else None
        train_schedule[i].append((s, arr, dep))

# Flight times
flight_times = {k: D_k[k] for k in K}

print("Train Timetable:")
for i, schedule in train_schedule.items():
    print(f"Train {i}:")
    for s, arr, dep in schedule:
        arr_str = f"{arr:.1f}" if arr is not None else "-"
        dep_str = f"{dep:.1f}" if dep is not None else "-"
        print(f"  Station {s}: Arrival = {arr_str}, Departure = {dep_str}")


print("Combined Timetable (Air-Rail):")
for i in I:
    print(f"\nTrain {i}:")
    for s, arr, dep in train_schedule[i]:
        arr_str = f"{arr:.1f}" if arr is not None else "-"
        dep_str = f"{dep:.1f}" if dep is not None else "-"
        print(f"  Station {s}: Arr = {arr_str}, Dep = {dep_str}")
    for k in K:
        if i in I_T and P[i, k].X > 0.5:
            print(f"  → Connects to Flight {k} at Transfer Station: Flight Dep = {D_k[k]}")

# -----------------------------
# DEFINE TIME STEPS FOR ANIMATION
# -----------------------------
time_steps = list(range(0, int(H)+1, 3))  # animate every 3 minutes
flight_display_time = 20

# -----------------------------
# HELPER: Compute edge offsets
# -----------------------------
def offset_points(x0, y0, x1, y1, num_trains, idx, spacing=0.03):
    dx = x1 - x0
    dy = y1 - y0
    length = np.sqrt(dx**2 + dy**2)
    if length == 0:
        return x0, y0, x1, y1
    px_u = -dy / length
    py_u = dx / length
    shift = (idx - (num_trains - 1) / 2) * spacing
    return x0 + px_u * shift, y0 + py_u * shift, x1 + px_u * shift, y1 + py_u * shift


# -----------------------------
# AUTOMATIC TRAIN COLOR MAP
# -----------------------------
base_palette = (
    px.colors.qualitative.Plotly +
    px.colors.qualitative.D3 +
    px.colors.qualitative.Set3 +
    px.colors.qualitative.Dark24 +
    px.colors.qualitative.Light24
)

train_colors = {}
train_names = {}

for i, train in enumerate(sorted(I)):
    train_colors[train] = base_palette[i % len(base_palette)]
    route_str = ",".join([f"S{s}" for s in S_i[train]])
    train_names[train] = f"Train {train}: {route_str}"


# -----------------------------
# Compute trains per edge
# -----------------------------
edge_trains = defaultdict(list)

for i in I:
    route = S_i[i]
    for idx in range(len(route) - 1):
        s, s_next = route[idx], route[idx + 1]
        edge_key = tuple(sorted((s, s_next)))
        edge_trains[edge_key].append(i)


# -----------------------------
# BASE STATIC NETWORK (NO DUPLICATE LEGENDS)
# -----------------------------
base_data = []
legend_added_for_train = set()

for (s, s_next), trains_on_edge in edge_trains.items():
    x0, y0 = station_coords[s]
    x1, y1 = station_coords[s_next]

    for idx, train in enumerate(trains_on_edge):
        ox0, oy0, ox1, oy1 = offset_points(
            x0, y0, x1, y1, len(trains_on_edge), idx
        )

        show_legend = train not in legend_added_for_train

        base_data.append(go.Scatter(
            x=[ox0, ox1],
            y=[oy0, oy1],
            mode='lines',
            line=dict(color=train_colors[train], width=4),
            name=train_names[train] if show_legend else None,
            legendgroup=f"Train {train}",
            hoverinfo='skip',
            showlegend=show_legend
        ))

        if show_legend:
            legend_added_for_train.add(train)


# -----------------------------
# Stations (clean legend)
# -----------------------------
legend_added = {"station": False, "airport": False}

for s, (x, y) in station_coords.items():
    is_airport = s in transfer_stations
    legend_name = "Airport" if is_airport else "Station"
    show_legend = not legend_added[legend_name.lower()]
    legend_added[legend_name.lower()] = True

    base_data.append(go.Scatter(
        x=[x],
        y=[y],
        mode="markers+text",
        marker=dict(
            size=16,
            symbol="triangle-up" if is_airport else "circle",
            color='red' if is_airport else 'skyblue'
        ),
        text=[f"S{s}"],
        textposition="top center",
        name=legend_name,
        showlegend=show_legend
    ))


# -----------------------------
# DYNAMIC TRAIN MARKERS (ONLY ONE LOOP)
# -----------------------------
train_traces = {}
flight_traces = {}
dynamic_data = []

for i in I:
    dynamic_data.append(go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(
            size=18,
            symbol="square",
            color=train_colors[i]
        ),
        legendgroup=f"Train {i}",
        showlegend=False
    ))

    train_traces[i] = len(base_data) + len(dynamic_data) - 1


# -----------------------------
# Flights
# -----------------------------
for k in K:
    dynamic_data.append(go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(size=22, symbol="star", color="gold"),
        name=f"Flight {k}"
    ))

    flight_traces[k] = len(base_data) + len(dynamic_data) - 1


# -----------------------------
# Create figure
# -----------------------------
fig = go.Figure(data=base_data + dynamic_data)

fig.update_layout(
    xaxis=dict(range=[-1, 7], autorange=False),
    yaxis=dict(range=[-1, 3], autorange=False)
)


# -----------------------------
# CREATE FRAMES
# -----------------------------
frames = []
dynamic_trace_indices = list(
    range(len(base_data), len(base_data) + len(dynamic_data))
)

for t in time_steps:

    frame_updates = [dict(x=[None], y=[None]) for _ in dynamic_data]

    for i in I:
        route = S_i[i]

        for idx in range(len(route) - 1):
            s, s_next = route[idx], route[idx + 1]

            if (i, s) in d and (i, s_next) in a:
                dep, arr = d[i, s].X, a[i, s_next].X

                if dep <= t <= arr:
                    lam = (t - dep) / (arr - dep)

                    edge_key = tuple(sorted((s, s_next)))
                    trains_on_edge = edge_trains[edge_key]
                    edge_idx = trains_on_edge.index(i)

                    x0, y0 = station_coords[s]
                    x1, y1 = station_coords[s_next]

                    x0o, y0o, x1o, y1o = offset_points(
                        x0, y0, x1, y1,
                        len(trains_on_edge),
                        edge_idx
                    )

                    x = x0o + lam * (x1o - x0o)
                    y = y0o + lam * (y1o - y0o)

                    trace_index = train_traces[i] - len(base_data)
                    frame_updates[trace_index] = dict(x=[x], y=[y])

    # Flights
    for k in K:
        if abs(t - D_k[k]) <= flight_display_time:
            st = flight_station[k]
            x, y = station_coords[st]
            trace_index = flight_traces[k] - len(base_data)
            frame_updates[trace_index] = dict(x=[x], y=[y])

    frames.append(go.Frame(
        data=frame_updates,
        traces=dynamic_trace_indices,
        name=str(t),
        layout=go.Layout(
            annotations=[dict(
                text=f"Time: {t}",
                x=0.01, y=0.99,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=18)
            )]
        )
    ))

fig.frames = frames


# -----------------------------
# SLIDER & PLAY BUTTON
# -----------------------------
sliders = [{
    "steps": [
        {
            "method": "animate",
            "args": [[str(t)],
                     {"frame": {"duration": 0, "redraw": False},
                      "mode": "immediate"}],
            "label": str(t)
        }
        for t in time_steps
    ],
    "transition": {"duration": 0},
    "x": 0.1,
    "len": 0.8
}]

fig.update_layout(
    title="Animated Air-Rail Synchronization (Multi-Edge Offsets)",
    updatemenus=[{
        "type": "buttons",
        "buttons": [{
            "label": "Play",
            "method": "animate",
            "args": [None,
                     {"frame": {"duration": 30, "redraw": False},
                      "fromcurrent": True,
                      "transition": {"duration": 0}}]
        }]
    }],
    sliders=sliders
)

fig.show()



















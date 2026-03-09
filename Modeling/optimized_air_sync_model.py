# -*- coding: utf-8 -*-
"""
Optimized Air-Rail Synchronization Model
Uses native multi-objective optimization and indicator constraints
"""

import sys
import gurobipy as gp
from gurobipy import GRB
from parameters_scandinavia import (
    I, beta, gamma, y, dwell_max, dwell_min,
    dw_lower, dw_upper, aw_lower, aw_upper,
    xs, xe, M, HS, HA, l_k, u_k,
    v1, v2, w1, w2, D_k,
    x, S, r, H,
    S_i, I_T, transfer_stations,
    ori_i, des_i, K_out, K_in, flight_station_out,
    flight_station_in, l_m, u_m, A_m
)

# ==========================================================
# MODEL CREATION
# ==========================================================

model = gp.Model("Air_HSR_Synchronization_Optimized")

# ==========================================================
# SOLVER PARAMETERS (IMPORTANT FOR PERFORMANCE)
# ==========================================================

# Set time limit per objective (adjust as needed)
model.Params.TimeLimit = 600  # 10 minutes max per phase

# Set MIP gap tolerance (1% is usually acceptable)
model.Params.MIPGap = 0.01

# Improve numerical stability with big-M constraints
model.Params.NumericFocus = 1

# Use more aggressive presolve for multi-objective
model.Params.MultiObjPre = 2

# Enable detailed logging
model.Params.OutputFlag = 1

# Use multiple threads efficiently
# model.Params.Threads = 8  # Uncomment and adjust if needed

print("Solver parameters set for improved performance.")

# ==========================================================
# DECISION VARIABLES
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

# P_{i,k} synchronization binary for OUTGOING flights
P = {}
for i in I_T:
    for k in K_out:
        P[i, k] = model.addVar(vtype=GRB.BINARY,
                               name=f"P_{i}_{k}")

# Q_{i,m} synchronization binary for INCOMING flights
Q = {}
for i in I_T:
    for m in K_in:
        Q[i, m] = model.addVar(vtype=GRB.BINARY,
                               name=f"Q_{i}_{m}")

# C_k outgoing flight synchronized
C = {}
for k in K_out:
    C[k] = model.addVar(vtype=GRB.BINARY,
                        name=f"C_{k}")

# C_in_m incoming flight synchronized
C_in = {}
for m in K_in:
    C_in[m] = model.addVar(vtype=GRB.BINARY,
                           name=f"C_in_{m}")

# p_{i,k} penalty variable for outgoing flights
p = {}
for i in I_T:
    for k in K_out:
        p[i, k] = model.addVar(lb=0, vtype=GRB.CONTINUOUS,
                               name=f"p_{i}_{k}")

# p_in_{i,m} penalty variable for incoming flights
p_in = {}
for i in I_T:
    for m in K_in:
        p_in[i, m] = model.addVar(lb=0, vtype=GRB.CONTINUOUS,
                                  name=f"p_in_{i}_{m}")

model.update()

print("Decision variables created.")

# ==========================================================
# OBJECTIVE FUNCTIONS (Multi-Objective Setup)
# ==========================================================

# Z1: Maximize total synchronizations (outgoing + incoming)
Z1 = gp.quicksum(P[i, k] for i in I_T for k in K_out) + \
     gp.quicksum(Q[i, m] for i in I_T for m in K_in)

# Z2: Maximize coverage (outgoing + incoming)
Z2 = gp.quicksum(C[k] for k in K_out) + \
     gp.quicksum(C_in[m] for m in K_in)

# Z3: Minimize penalties (outgoing + incoming)
Z3 = gp.quicksum(p[i, k] for i in I_T for k in K_out) + \
     gp.quicksum(p_in[i, m] for i in I_T for m in K_in)

# Set hierarchical multi-objective with priorities
# Priority 2 (highest): Maximize synchronizations
# Priority 1 (medium): Maximize coverage
# Priority 0 (lowest): Minimize penalties
model.ModelSense = GRB.MAXIMIZE
model.setObjectiveN(Z1, index=0, priority=2, name="Synchronizations")
model.setObjectiveN(Z2, index=1, priority=1, name="Coverage")
model.setObjectiveN(-Z3, index=2, priority=0, name="Penalties")  # Negate to minimize

print("Multi-objective hierarchy configured: Synchronizations (P2) > Coverage (P1) > Penalties (P0)")

# ==========================================================
# CONSTRAINTS
# ==========================================================

print("Adding constraints...")

# Running time constraints (minimum)
for i in I:
    stations = S_i[i]
    for idx in range(len(stations) - 1):
        s = stations[idx]
        s_next = stations[idx + 1]
        model.addConstr(
            a[i, s_next] - d[i, s] >=
            r[i, s] + beta[i, s] * x[i, s] + gamma[i, s_next] * x[i, s_next],
            name=f"run_min_{i}_{s}"
        )

# Running time constraints (maximum)
for i in I:
    stations = S_i[i]
    for idx in range(len(stations) - 1):
        s = stations[idx]
        s_next = stations[idx + 1]
        model.addConstr(
            a[i, s_next] - d[i, s] <=
            r[i, s] + beta[i, s] * x[i, s] + gamma[i, s_next] * x[i, s_next] + y[i, s],
            name=f"run_max_{i}_{s}"
        )

# Dwell time constraints (minimum)
for i in I:
    for s in S_i[i]:
        if s not in [ori_i[i], des_i[i]]:
            model.addConstr(
                d[i, s] - a[i, s] >= dwell_min[i, s] * x[i, s],
                name=f"dwell_min_{i}_{s}"
            )

# Dwell time constraints (maximum)
for i in I:
    for s in S_i[i]:
        if s not in [ori_i[i], des_i[i]]:
            model.addConstr(
                d[i, s] - a[i, s] <= dwell_max[i, s] * x[i, s],
                name=f"dwell_max_{i}_{s}"
            )

# Departure window constraints
for i in I:
    model.addConstr(
        d[i, ori_i[i]] >= dw_lower[i],
        name=f"dep_window_low_{i}"
    )
    model.addConstr(
        d[i, ori_i[i]] <= dw_upper[i],
        name=f"dep_window_up_{i}"
    )

# Arrival window constraints
for i in I:
    model.addConstr(
        a[i, des_i[i]] >= aw_lower[i],
        name=f"arr_window_low_{i}"
    )
    model.addConstr(
        a[i, des_i[i]] <= aw_upper[i],
        name=f"arr_window_up_{i}"
    )

# Departure headway constraints
for i in I:
    for j in I:
        if i != j and (i, j) in xs:
            stations_i = S_i[i]
            stations_j = S_i[j]
            common = sorted(list(set(stations_i).intersection(set(stations_j))))
            
            for idx in range(len(common) - 1):
                s = common[idx]
                if s != des_i[i] and s != des_i[j]:
                    model.addConstr(
                        d[j, s] - d[i, s] + M * (1 - O[i, j, s]) >= HS[s],
                        name=f"dep_headway1_{i}_{j}_{s}"
                    )
                    model.addConstr(
                        d[i, s] - d[j, s] + M * O[i, j, s] >= HS[s],
                        name=f"dep_headway2_{i}_{j}_{s}"
                    )

# Arrival headway constraints
for i in I:
    for j in I:
        if i != j and (i, j) in xs:
            stations_i = S_i[i]
            stations_j = S_i[j]
            common = sorted(list(set(stations_i).intersection(set(stations_j))))
            
            for idx in range(len(common) - 1):
                s = common[idx]
                s_next = common[idx + 1]
                if s_next != ori_i[i] and s_next != ori_i[j]:
                    model.addConstr(
                        a[j, s_next] - a[i, s_next] + M * (1 - O[i, j, s]) >= HA[s_next],
                        name=f"arr_headway1_{i}_{j}_{s}"
                    )
                    model.addConstr(
                        a[i, s_next] - a[j, s_next] + M * O[i, j, s] >= HA[s_next],
                        name=f"arr_headway2_{i}_{j}_{s}"
                    )

# Ordering constraints
for i in I:
    for j in I:
        if i < j:
            common = set(S_i[i]).intersection(set(S_i[j]))
            for s in common:
                model.addConstr(
                    O[i, j, s] + O[j, i, s] == 1,
                    name=f"ordering_{i}_{j}_{s}"
                )

print("Basic constraints added.")

# ==========================================================
# OUTGOING FLIGHT SYNCHRONIZATION (USING INDICATOR CONSTRAINTS)
# ==========================================================

print("Adding outgoing flight synchronization constraints (indicator-based)...")

for i in I_T:
    for k in K_out:
        st_k = flight_station_out[k]
        
        if st_k in S_i[i] and st_k != ori_i[i]:
            # When P[i,k] = 1, enforce: l_k <= a[i, st_k] <= u_k
            model.addGenConstrIndicator(
                P[i, k], True, a[i, st_k] >= l_k[k],
                name=f"sync_out_low_{i}_{k}"
            )
            model.addGenConstrIndicator(
                P[i, k], True, a[i, st_k] <= u_k[k],
                name=f"sync_out_up_{i}_{k}"
            )
        else:
            # Invalid combination - force P[i,k] = 0
            model.addConstr(
                P[i, k] == 0,
                name=f"sync_out_invalid_{i}_{k}"
            )

# ==========================================================
# INCOMING FLIGHT SYNCHRONIZATION (USING INDICATOR CONSTRAINTS)
# ==========================================================

print("Adding incoming flight synchronization constraints (indicator-based)...")

for i in I_T:
    for m in K_in:
        st_m = flight_station_in[m]
        
        if st_m in S_i[i] and st_m != des_i[i]:
            # When Q[i,m] = 1, enforce: l_m <= d[i, st_m] <= u_m
            model.addGenConstrIndicator(
                Q[i, m], True, d[i, st_m] >= l_m[m],
                name=f"sync_in_low_{i}_{m}"
            )
            model.addGenConstrIndicator(
                Q[i, m], True, d[i, st_m] <= u_m[m],
                name=f"sync_in_up_{i}_{m}"
            )
        else:
            # Invalid combination - force Q[i,m] = 0
            model.addConstr(
                Q[i, m] == 0,
                name=f"sync_in_invalid_{i}_{m}"
            )

# ==========================================================
# COVERAGE CONSTRAINTS
# ==========================================================

print("Adding coverage constraints...")

# Outgoing flights
for k in K_out:
    model.addConstr(
        C[k] <= gp.quicksum(P[i, k] for i in I_T),
        name=f"coverage_out_{k}"
    )

# Incoming flights
for m in K_in:
    model.addConstr(
        C_in[m] <= gp.quicksum(Q[i, m] for i in I_T),
        name=f"coverage_in_{m}"
    )

# ==========================================================
# PENALTY CONSTRAINTS (USING INDICATOR CONSTRAINTS)
# ==========================================================

print("Adding penalty constraints (indicator-based)...")

# Outgoing flights
mid_k = {k: (l_k[k] + u_k[k]) / 2 for k in K_out}

for i in I_T:
    for k in K_out:
        st_k = flight_station_out[k]
        
        if st_k in S_i[i] and st_k != ori_i[i]:
            # When P[i,k] = 1, enforce penalty constraints
            # Business passengers (prefer later arrival)
            model.addGenConstrIndicator(
                P[i, k], True, 
                p[i, k] >= v1 * w1 * (a[i, st_k] - mid_k[k]),
                name=f"penalty_out_business_{i}_{k}"
            )
            # Leisure passengers (prefer earlier arrival)
            model.addGenConstrIndicator(
                P[i, k], True,
                p[i, k] >= v2 * w2 * (mid_k[k] - a[i, st_k]),
                name=f"penalty_out_leisure_{i}_{k}"
            )
            # When P[i,k] = 0, penalty must be 0
            model.addGenConstrIndicator(
                P[i, k], False,
                p[i, k] == 0,
                name=f"penalty_out_zero_{i}_{k}"
            )
        else:
            model.addConstr(
                p[i, k] == 0,
                name=f"penalty_out_invalid_{i}_{k}"
            )

# Incoming flights
mid_m = {m: (l_m[m] + u_m[m]) / 2 for m in K_in}

for i in I_T:
    for m in K_in:
        st_m = flight_station_in[m]
        
        if st_m in S_i[i] and st_m != des_i[i]:
            # When Q[i,m] = 1, enforce penalty constraints
            # Business passengers (prefer earlier departure)
            model.addGenConstrIndicator(
                Q[i, m], True,
                p_in[i, m] >= v1 * w1 * (d[i, st_m] - mid_m[m]),
                name=f"penalty_in_business_{i}_{m}"
            )
            # Leisure passengers (prefer later departure)
            model.addGenConstrIndicator(
                Q[i, m], True,
                p_in[i, m] >= v2 * w2 * (mid_m[m] - d[i, st_m]),
                name=f"penalty_in_leisure_{i}_{m}"
            )
            # When Q[i,m] = 0, penalty must be 0
            model.addGenConstrIndicator(
                Q[i, m], False,
                p_in[i, m] == 0,
                name=f"penalty_in_zero_{i}_{m}"
            )
        else:
            model.addConstr(
                p_in[i, m] == 0,
                name=f"penalty_in_invalid_{i}_{m}"
            )

print("All constraints added successfully.")
model.update()

# ==========================================================
# SOLVE (Single Optimize Call for All Objectives)
# ==========================================================

print("\n" + "="*70)
print("SOLVING HIERARCHICAL MULTI-OBJECTIVE MODEL")
print("="*70)

model.optimize()

# ==========================================================
# CHECK SOLUTION STATUS
# ==========================================================

if model.Status == GRB.OPTIMAL:
    print("\n" + "="*70)
    print("OPTIMAL SOLUTION FOUND FOR ALL OBJECTIVES")
    print("="*70)
elif model.Status == GRB.TIME_LIMIT:
    print("\n" + "="*70)
    print("TIME LIMIT REACHED - BEST SOLUTION FOUND SO FAR")
    print("="*70)
elif model.Status == GRB.INFEASIBLE:
    print("\nERROR: Model is infeasible!")
    model.computeIIS()
    model.write("model_iis.ilp")
    print("IIS written to model_iis.ilp")
    sys.exit()
else:
    print(f"\nERROR: Optimization failed with status {model.Status}")
    sys.exit()

# ==========================================================
# EXTRACT RESULTS
# ==========================================================

# Extract objective values
Z1_val = sum(P[i, k].X for i in I_T for k in K_out) + sum(Q[i, m].X for i in I_T for m in K_in)
Z2_val = sum(C[k].X for k in K_out) + sum(C_in[m].X for m in K_in)
Z3_val = sum(p[i, k].X for i in I_T for k in K_out) + sum(p_in[i, m].X for i in I_T for m in K_in)

print(f"\nZ1 (Total Synchronizations) = {Z1_val:.0f}")
print(f"  - Outgoing (Train→Flight): {sum(P[i,k].X for i in I_T for k in K_out):.0f}")
print(f"  - Incoming (Flight→Train): {sum(Q[i,m].X for i in I_T for m in K_in):.0f}")

print(f"\nZ2 (Total Coverage) = {Z2_val:.0f}")
print(f"  - Outgoing flights covered: {sum(C[k].X for k in K_out):.0f}/{len(K_out)}")
print(f"  - Incoming flights covered: {sum(C_in[m].X for m in K_in):.0f}/{len(K_in)}")

print(f"\nZ3 (Total Penalty) = {Z3_val:.2f}")

# ==========================================================
# DISPLAY DETAILED RESULTS
# ==========================================================

print("\n" + "="*70)
print("OUTGOING FLIGHT SYNCHRONIZATIONS (Train → Flight)")
print("="*70)
outgoing_count = 0
for i in I_T:
    for k in K_out:
        if P[i, k].X > 0.5:
            st_k = flight_station_out[k]
            outgoing_count += 1
            print(f"  Train {i} → Flight {k} at Station {st_k}: "
                  f"train_arr={a[i,st_k].X:.1f}, flight_dep={D_k[k]}, "
                  f"transfer={D_k[k]-a[i,st_k].X:.1f}min, penalty={p[i,k].X:.2f}")
print(f"Total outgoing synchronizations: {outgoing_count}")

print("\n" + "="*70)
print("INCOMING FLIGHT SYNCHRONIZATIONS (Flight → Train)")
print("="*70)
incoming_count = 0
for i in I_T:
    for m in K_in:
        if Q[i, m].X > 0.5:
            st_m = flight_station_in[m]
            incoming_count += 1
            print(f"  Flight {m} → Train {i} at Station {st_m}: "
                  f"flight_arr={A_m[m]}, train_dep={d[i,st_m].X:.1f}, "
                  f"transfer={d[i,st_m].X-A_m[m]:.1f}min, penalty={p_in[i,m].X:.2f}")
print(f"Total incoming synchronizations: {incoming_count}")

print("\n" + "="*70)
print("TRAIN TIMETABLE")
print("="*70)
for i in I:
    print(f"Train {i}:")
    for s in S_i[i]:
        arr_str = f"{a[i, s].X:.1f}" if (i, s) in a else "-"
        dep_str = f"{d[i, s].X:.1f}" if (i, s) in d else "-"
        print(f"  Station {s}: Arr = {arr_str}, Dep = {dep_str}")

print("\n" + "="*70)
print("OPTIMIZATION COMPLETE")
print("="*70)

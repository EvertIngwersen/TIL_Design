# -*- coding: utf-8 -*-
"""
parameters_bidirectional.py

Parameters for HSR-Airport integration model with BIDIRECTIONAL transfers.
Includes both outgoing and incoming flights.
"""

# ==========================================================
# 0. STATIONS
# ==========================================================
stations = {
    1: {"coords": (0, 0)},
    2: {"coords": (1, 0.5)},
    3: {"coords": (2, 1), "airport": True},
    4: {"coords": (3, 0.5)},
    5: {"coords": (4, 1), "airport": True},
    6: {"coords": (4, 0.5), "airport": True},
    7: {"coords": (1,1.5)},
    8: {"coords": (0.5, 2)},
    9: {"coords": (4.5, 0), "airport": True},
    10:{"coords": (5.5, 0.5), "airport": True},
    11:{"coords": (2, 2.5)},
    12:{"coords": (2, 0)},
    13:{"coords": (3, -0.5)},
    14:{"coords": (3, 2.5)},
    15:{"coords": (4, 2.5)},
    16:{"coords": (5, 2.5)},
}

S = list(stations.keys())
transfer_stations = [s for s, info in stations.items() if info.get("airport")]

# ==========================================================
# 1. FLIGHTS - UPDATED WITH INCOMING AND OUTGOING
# ==========================================================

# Outgoing flights (passengers arrive by train, depart by flight)
outgoing_flights = {
    1: {"station": 3, "departure": 560},
    2: {"station": 3, "departure": 630},
    3: {"station": 5, "departure": 710},
    4: {"station": 6, "departure": 740},
    5: {"station": 6, "departure": 710},
    6: {"station": 3, "departure": 720},
    7: {"station": 9, "departure": 590},
    8: {"station": 10, "departure": 600},
    9: {"station": 10, "departure": 1000},
    10: {"station": 10, "departure": 1200},
    11: {"station": 3, "departure": 255},
    12: {"station": 5, "departure": 1250}
}

# Incoming flights (passengers arrive by flight, depart by train)
incoming_flights = {
    1: {"station": 3, "arrival": 480},
    2: {"station": 5, "arrival": 520},
    3: {"station": 6, "arrival": 550},
    4: {"station": 9, "arrival": 500},
    5: {"station": 10, "arrival": 530},
    6: {"station": 3, "arrival": 650},
    7: {"station": 5, "arrival": 700},
    8: {"station": 3, "arrival": 600},
    9: {"station": 3, "arrival": 515},
    10: {"station": 10, "arrival": 650},
    11: {"station": 10, "arrival": 700},
    12: {"station": 5, "arrival": 950},
}

# Sets
K_out = list(outgoing_flights.keys())
K_in = list(incoming_flights.keys())
K = K_out + K_in  # Combined for compatibility

# Flight station mapping
flight_station_out = {k: outgoing_flights[k]["station"] for k in K_out}
flight_station_in = {m: incoming_flights[m]["station"] for m in K_in}
flight_station = {**flight_station_out, **flight_station_in}

# Times
D_k = {k: outgoing_flights[k]["departure"] for k in K_out}
A_m = {m: incoming_flights[m]["arrival"] for m in K_in}

# Transfer window bounds
b_min = 20
b_max = 70

# Connection windows for OUTGOING flights (train arrival must be in this window)
l_k = {k: D_k[k] - b_max for k in K_out}
u_k = {k: D_k[k] - b_min for k in K_out}

# Connection windows for INCOMING flights (train departure must be in this window)
l_m = {m: A_m[m] + b_min for m in K_in}
u_m = {m: A_m[m] + b_max for m in K_in}

# ==========================================================
# 2. TRAINS
# ==========================================================
trains = {
    1: {"route": [1, 2, 3, 4], "origin": 1, "dest": 4},
    2: {"route": [1, 3, 4], "origin": 1, "dest": 4},
    3: {"route": [2, 3, 4, 9, 10], "origin": 2, "dest": 10},
    4: {"route": [1, 3, 5, 6], "origin": 1, "dest": 6},
    5: {"route": [2, 3, 6], "origin": 2, "dest": 6},
    6: {"route": [6, 5, 3], "origin": 6, "dest": 3},
    7: {"route": [1, 8, 7, 2, 3], "origin": 1, "dest": 3},
    8: {"route": [4, 9, 5, 6], "origin": 4, "dest": 6},
    9: {"route": [2, 3, 5, 10], "origin": 2, "dest": 10},
    10: {"route": [16, 15, 14, 11, 3, 12, 13, 9, 10], "origin": 16, "dest": 10},
    11: {"route": [9,10], "origin": 9, "dest": 10}
}

I = list(trains.keys())
S_i = {i: trains[i]["route"] for i in I}
ori_i = {i: trains[i]["origin"] for i in I}
des_i = {i: trains[i]["dest"] for i in I}

# Trains serving airport stations vs non-airport
I_T = [i for i in I if any(s in transfer_stations for s in S_i[i])]
I_N = [i for i in I if i not in I_T]

# ==========================================================
# 3. TRAVEL & TIMING PARAMETERS
# ==========================================================
travel_times = {
    # Original forward directions
    (1,2): 20, (2,3): 25, (3,4): 30,
    (1,3): 35, (2,4): 40, (4,5): 18, (5,6): 22,
    (3,5): 28, (3,6): 40, (8,7): 10,
    (6,5): 22, (11,3): 40, (3,12): 15,
    (5,3): 28, (12,13): 25, (13,9): 10, (9,10): 20,
    (16,15):40, (15,14): 30, (14,11): 30}

travel_times.update({
    (1,8): 15, (8,2): 15,
    (4,9): 12, (9,5): 12,
    (5,10): 20, (3,10): 25,
    
    # reverse directions
    (8,1): 15, (2,8): 15,
    (9,4): 12, (5,9): 12,
    (10,5): 20, (10,3): 25,
})

# Running times, acceleration, deceleration, dwell times
r, beta, gamma, y, x = {}, {}, {}, {}, {}
dwell_min, dwell_max = {}, {}

for i in I:
    route = S_i[i]
    origin = ori_i[i]
    dest = des_i[i]
    for idx, s in enumerate(route):
        # Running times
        if idx < len(route) - 1:
            s_next = route[idx + 1]
            r[i, s] = travel_times.get((s, s_next), 30)
            y[i, s] = 5  # time supplement
            beta[i, s] = 2  # acceleration
        # Deceleration for next station
        if s != origin:
            gamma[i, s] = 3
        # Stop decision
        x[i, s] = 1
        # Dwell times (not at origin/dest)
        if s not in [origin, dest]:
            dwell_min[i, s] = 2
            dwell_max[i, s] = 6

# Headways
HA = {s: 3 for s in S}
HS = {s: 3 for s in S}

# Departure/arrival windows
wt = {i: 200 for i in I}
dw_lower = {i: 0 for i in I}
dw_upper = {i: 1400 for i in I}
aw_lower = {i: 0 for i in I}
aw_upper = {i: 1400 for i in I}

# Original timetable
a_o, d_o = {}, {}
for i in I:
    route = S_i[i]
    base_time = 480 + 20 * i
    cumulative_time = base_time
    
    for idx, s in enumerate(route):
        if s != des_i[i]:
            d_o[i, s] = cumulative_time
        if s != ori_i[i]:
            a_o[i, s] = cumulative_time
        if idx < len(route) - 1:
            s_next = route[idx + 1]
            travel_time = r[i, s]
            cumulative_time += travel_time + 5

# Planning horizon and passenger sensitivity
v1, v2 = 2.0, 1.0
w2 = 0.4
w1 = 1 - w2
H = 1440
M = H + max(max(HS.values()), max(HA.values()))
M_prime = H
M_double = H * max(v1*w1, v2*w2)

# Shared station intervals
xs, xe = {}, {}
for i in I:
    for j in I:
        if i != j:
            common = sorted(list(set(S_i[i]).intersection(S_i[j])))
            if len(common) >= 2:
                xs[i,j] = common[0]
                xe[i,j] = common[-1]

# Convenience dict for station coordinates
station_coords = {s: info["coords"] for s, info in stations.items()}

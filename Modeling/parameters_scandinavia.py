# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 13:25:40 2026

@author: evert
"""

# ALL TIME VALUES ARE IN MINUTES

# ==========================================================
# 0. STATIONS
# ==========================================================
stations = {
    1: {"coords": (17.9331197, 59.652312), "airport": True},   #Arlanda Airport
    2: {"coords": (12.6494168, 55.6296397), "airport": True},  #Kastrup Airport
    3: {"coords": (11.0967803, 60.1929196), "airport": True}   #Gardermoen Airport
    }

S = list(stations.keys())
transfer_stations = [s for s, info in stations.items() if info.get("airport")]

# Outgoing flights (passengers arrive by train, depart by flight)

# PLACEHOLDER VALUES

outgoing_flights = {
    1: {"station": 1, "departure": 560},
    2: {"station": 1, "departure": 630},
    3: {"station": 1, "departure": 710},
    4: {"station": 1, "departure": 740},
    5: {"station": 2, "departure": 710},
    6: {"station": 2, "departure": 720},
    7: {"station": 2, "departure": 590},
    8: {"station": 2, "departure": 600},
    9: {"station": 3, "departure": 1000},
    10: {"station": 3, "departure": 1200},
    11: {"station": 3, "departure": 255},
    12: {"station": 3, "departure": 1250}
}

# Incoming flights (passengers arrive by flight, depart by train)
incoming_flights = {
    1: {"station": 1, "arrival": 480},
    2: {"station": 1, "arrival": 520},
    3: {"station": 1, "arrival": 550},
    4: {"station": 1, "arrival": 500},
    5: {"station": 2, "arrival": 530},
    6: {"station": 2, "arrival": 650},
    7: {"station": 2, "arrival": 700},
    8: {"station": 2, "arrival": 600},
    9: {"station": 3, "arrival": 515},
    10: {"station": 3, "arrival": 650},
    11: {"station": 3, "arrival": 700},
    12: {"station": 3, "arrival": 950},
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
    1: {"route": [1, 2], "origin": 1, "dest": 2},
    2: {"route": [2, 1], "origin": 2, "dest": 1},
    3: {"route": [1, 3], "origin": 1, "dest": 3},
    4: {"route": [3, 1], "origin": 3, "dest": 1},
    5: {"route": [3, 2], "origin": 3, "dest": 2},
    6: {"route": [2, 3], "origin": 2, "dest": 3}
}

I = list(trains.keys())
S_i = {i: trains[i]["route"] for i in I}
ori_i = {i: trains[i]["origin"] for i in I}
des_i = {i: trains[i]["dest"] for i in I}

# Trains serving airport stations vs non-airport
I_T = [i for i in I if any(s in transfer_stations for s in S_i[i])]
I_N = [i for i in I if i not in I_T]


# ==========================================================
# 3. TRAVEL & TIMING PARAMETERS (assumed time(u,v) = time(v,u))
# ==========================================================
travel_times = {
    (1,2): 229, (1,3): 251,
    (2, 1): 229, (2,3): 293,
    (3,1): 251, (3,2): 293
    }

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
H = 1440  # One full day 24*60 = 1440 minutes
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






















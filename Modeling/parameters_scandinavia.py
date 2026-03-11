# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 13:25:40 2026

@author: evert
"""

import random
import numpy as np

# ALL TIME VALUES ARE IN MINUTES

# ==========================================================
# 0. STATIONS
# ==========================================================
stations = {
    1: {"coords": (5, 1.5), "airport": True},   #Arlanda Airport
    2: {"coords": (3, -0.5), "airport": True},  #Kastrup Airport
    3: {"coords": (2,1), "airport": True}   #Gardermoen Airport
    }

S = list(stations.keys())
transfer_stations = [s for s, info in stations.items() if info.get("airport")]

# Outgoing flights (passengers arrive by train, depart by flight)

def generate_outgoing_flights_per_airport_random(airport_settings, max_variation=5):
    """
    Generates a dictionary of outgoing flights for multiple airports with individual settings,
    adding a small random variation to each departure.

    Parameters:
        airport_settings (dict):
            Keys are airport IDs.
            Values are dicts with 'num_flights', 'start_time', 'end_time' in minutes from midnight.

        max_variation (int): Maximum random deviation (in minutes) from the scheduled departure.

    Returns:
        dict: Dictionary of flights with flight_id as key and station + departure info as value.
    """
    outgoing_flights = {}
    flight_id = 1

    for airport, settings in airport_settings.items():
        num_flights = settings['num_flights']
        start_time = settings['start_time']
        end_time = settings['end_time']

        if num_flights == 1:
            departures = [start_time]
        else:
            interval = (end_time - start_time) / (num_flights - 1)
            departures = [start_time + i * interval for i in range(num_flights)]

        for dep in departures:
            # Add random variation
            dep_random = int(dep + random.randint(-max_variation, max_variation))
            outgoing_flights[flight_id] = {"station": airport, "departure": dep_random}
            flight_id += 1

    return outgoing_flights

airport_settings_outgoing = {
    1: {'num_flights': 20, 'start_time': 420, 'end_time': 1380},
    2: {'num_flights': 20, 'start_time': 480, 'end_time': 1320},
    3: {'num_flights': 20, 'start_time': 450, 'end_time': 1200},
}

outgoing_flights = generate_outgoing_flights_per_airport_random(airport_settings_outgoing, max_variation=5)

# Incoming flights (passengers arrive by flight, depart by train)
def generate_incoming_flights_per_airport_random(airport_settings, max_variation=5):
    """
    Generates a dictionary of incoming flights for multiple airports with individual settings,
    adding a small random variation to each arrival.

    Parameters:
        airport_settings (dict):
            Keys are airport IDs.
            Values are dicts with 'num_flights', 'start_time', 'end_time' in minutes from midnight.

            Example:
            {
                1: {'num_flights': 20, 'start_time': 420, 'end_time': 1380},
                2: {'num_flights': 15, 'start_time': 480, 'end_time': 1320},
                3: {'num_flights': 10, 'start_time': 450, 'end_time': 1200},
            }

        max_variation (int): Maximum random deviation (in minutes) from the scheduled arrival.

    Returns:
        dict: Dictionary of flights with flight_id as key and station + arrival info as value.
    """
    incoming_flights = {}
    flight_id = 1

    for airport, settings in airport_settings.items():
        num_flights = settings['num_flights']
        start_time = settings['start_time']
        end_time = settings['end_time']

        if num_flights == 1:
            arrivals = [start_time]
        else:
            interval = (end_time - start_time) / (num_flights - 1)
            arrivals = [start_time + i * interval for i in range(num_flights)]

        for arr in arrivals:
            # Add random variation
            arr_random = int(arr + random.randint(-max_variation, max_variation))
            incoming_flights[flight_id] = {"station": airport, "arrival": arr_random}
            flight_id += 1

    return incoming_flights

# Example usage:
airport_settings_incoming = {
    1: {'num_flights': 7, 'start_time': 420, 'end_time': 1380},  # 7:00 - 23:00
    2: {'num_flights': 7, 'start_time': 480, 'end_time': 1320},  # 8:00 - 22:00
    3: {'num_flights': 7, 'start_time': 450, 'end_time': 1200},  # 7:30 - 20:00
}

incoming_flights = generate_incoming_flights_per_airport_random(airport_settings_incoming, max_variation=5)

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
# Original train dictionary
trains = {
    1: {"route": [1, 2], "origin": 1, "dest": 2},
    2: {"route": [2, 1], "origin": 2, "dest": 1},
    3: {"route": [1, 3], "origin": 1, "dest": 3},
    4: {"route": [3, 1], "origin": 3, "dest": 1},
    5: {"route": [3, 2], "origin": 3, "dest": 2},
    6: {"route": [2, 3], "origin": 2, "dest": 3}
}

# How many extra trains per route
extra_per_route = 0

# Find the current max train ID to continue numbering
max_id = max(trains.keys())

new_trains = {}

for train_id, info in trains.items():
    for i in range(extra_per_route):
        max_id += 1
        new_trains[max_id] = {
            "route": info["route"].copy(),
            "origin": info["origin"],
            "dest": info["dest"]
        }

# Merge the new trains into the original dictionary
trains.update(new_trains)


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

# ==========================================================
# IMPROVED DEPARTURE WINDOW HEURISTIC
# ==========================================================

# Flight time range
earliest_flight = min(min(D_k.values()), min(A_m.values()))
latest_flight = max(max(D_k.values()), max(A_m.values()))

print(f"Flight time range: {earliest_flight} to {latest_flight} minutes")
print(f"                   ({earliest_flight//60}:{earliest_flight%60:02d} to {latest_flight//60}:{latest_flight%60:02d})")

# Calculate optimal train departure spread
num_trains = len(I)

# IMPROVED: Start closer to first flights, not 5 hours before
planning_start = max(0, earliest_flight - 200)  # 3.3 hours before first flight
planning_end = min(1440, latest_flight - 150)   # Ensure trains can catch last flights

# IMPROVED: Wider windows for more flexibility
window_width = 180  # 3 hours instead of 2

# HEURISTIC: Spread trains evenly across the planning horizon
departure_spread = (planning_end - planning_start) / num_trains

dw_lower = {}
dw_upper = {}
aw_lower = {}
aw_upper = {}

print(f"\n{'='*70}")
print("IMPROVED TRAIN DEPARTURE WINDOWS")
print(f"{'='*70}")
print(f"Planning horizon: {planning_start:.0f}-{planning_end:.0f} min "
      f"({planning_start//60:02d}:{int(planning_start)%60:02d}-{planning_end//60:02d}:{int(planning_end)%60:02d})")
print(f"Window width: {window_width} minutes ({window_width/60:.1f} hours)")
print(f"{'='*70}")

for idx, i in enumerate(I):
    # Calculate target departure time for this train
    target_departure = planning_start + (idx * departure_spread)
    
    # Create window around target
    dw_lower[i] = max(0, target_departure - window_width/2)
    dw_upper[i] = min(1440, target_departure + window_width/2)
    
    # Arrival windows (based on max travel time + window width)
    max_travel = max(r.values()) + 50
    aw_lower[i] = max(0, dw_lower[i] + max_travel - window_width)
    aw_upper[i] = min(1440, dw_upper[i] + max_travel + window_width)
    
    print(f"Train {i:2d}: Depart {int(dw_lower[i]):4d}-{int(dw_upper[i]):4d} min "
          f"({int(dw_lower[i])//60:02d}:{int(dw_lower[i])%60:02d}-{int(dw_upper[i])//60:02d}:{int(dw_upper[i])%60:02d})")

print(f"{'='*70}\n")


# Original timetable (now serves as reference, not constraint)
a_o, d_o = {}, {}
for i in I:
    route = S_i[i]
    # Use the center of the departure window as reference
    base_time = (dw_lower[i] + dw_upper[i]) / 2
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

# Rest of parameters stay the same
wt = {i: window_width for i in I}  # Window width now matches actual windows

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

# ==========================================================
# PASSENGER DEMAND DATA
# ==========================================================

# Demand modeling approach selector
DEMAND_MODEL = "TIME_BASED"  # Options: "UNIFORM", "TIME_BASED", "SIZE_BASED", "TIME_AND_SIZE", "REALISTIC"

print(f"\n{'='*70}")
print(f"DEMAND MODELING: {DEMAND_MODEL}")
print(f"{'='*70}\n")

# -----------------------------
# DEMAND MODEL 1: UNIFORM (Baseline)
# -----------------------------
if DEMAND_MODEL == "UNIFORM":
    # All flights have equal demand (no prioritization)
    demand_out = {k: 100 for k in K_out}
    demand_in = {m: 100 for m in K_in}
    print("All flights treated equally (demand = 100)")

# -----------------------------
# DEMAND MODEL 2: TIME-BASED
# -----------------------------
elif DEMAND_MODEL == "TIME_BASED":
    # Demand varies by time of day
    # Peak hours: 7-9 AM, 5-7 PM (business travel)
    # Off-peak: other times
    
    demand_out = {}
    for k in K_out:
        dep_time = D_k[k]
        dep_hour = dep_time / 60
        
        # Morning peak (6-9 AM): High demand
        if 6 <= dep_hour < 9:
            demand_out[k] = 200
        # Evening peak (5-8 PM): High demand
        elif 17 <= dep_hour < 20:
            demand_out[k] = 180
        # Midday (9 AM - 5 PM): Medium demand
        elif 9 <= dep_hour < 17:
            demand_out[k] = 120
        # Early morning / late night: Low demand
        else:
            demand_out[k] = 50
    
    demand_in = {}
    for m in K_in:
        arr_time = A_m[m]
        arr_hour = arr_time / 60
        
        # Similar logic for arrivals
        if 6 <= arr_hour < 9:
            demand_in[m] = 200
        elif 17 <= arr_hour < 20:
            demand_in[m] = 180
        elif 9 <= arr_hour < 17:
            demand_in[m] = 120
        else:
            demand_in[m] = 50
    
    print("Demand based on time of day:")
    print("  Peak hours (6-9 AM, 5-8 PM): 180-200 passengers")
    print("  Midday (9 AM-5 PM): 120 passengers")
    print("  Off-peak: 50 passengers")

# -----------------------------
# DEMAND MODEL 3: AIRPORT SIZE-BASED
# -----------------------------
elif DEMAND_MODEL == "SIZE_BASED":
    # Demand based on airport importance
    # Arlanda (Stockholm) > Kastrup (Copenhagen) > Gardermoen (Oslo)
    
    airport_multipliers = {
        1: 1.5,   # Arlanda (largest)
        2: 1.2,   # Kastrup
        3: 1.0    # Gardermoen
    }
    
    base_demand = 100
    
    demand_out = {k: int(base_demand * airport_multipliers[flight_station_out[k]]) 
                  for k in K_out}
    demand_in = {m: int(base_demand * airport_multipliers[flight_station_in[m]]) 
                 for m in K_in}
    
    print("Demand based on airport size:")
    for airport, mult in airport_multipliers.items():
        print(f"  Airport {airport}: {mult}× base demand")

# -----------------------------
# DEMAND MODEL 4: TIME + SIZE COMBINED
# -----------------------------
elif DEMAND_MODEL == "TIME_AND_SIZE":
    # Combines time-of-day and airport size effects
    
    airport_multipliers = {
        1: 1.4,   # Arlanda
        2: 1.2,   # Kastrup  
        3: 1.0    # Gardermoen
    }
    
    demand_out = {}
    for k in K_out:
        dep_time = D_k[k]
        dep_hour = dep_time / 60
        airport = flight_station_out[k]
        
        # Base demand by time
        if 6 <= dep_hour < 9 or 17 <= dep_hour < 20:
            base = 150  # Peak
        elif 9 <= dep_hour < 17:
            base = 100  # Midday
        else:
            base = 40   # Off-peak
        
        # Apply airport multiplier
        demand_out[k] = int(base * airport_multipliers[airport])
    
    demand_in = {}
    for m in K_in:
        arr_time = A_m[m]
        arr_hour = arr_time / 60
        airport = flight_station_in[m]
        
        if 6 <= arr_hour < 9 or 17 <= arr_hour < 20:
            base = 150
        elif 9 <= arr_hour < 17:
            base = 100
        else:
            base = 40
        
        demand_in[m] = int(base * airport_multipliers[airport])
    
    print("Demand based on time + airport size:")
    print("  Peak × Large Airport: ~210 passengers")
    print("  Peak × Medium Airport: ~180 passengers")
    print("  Midday × Large Airport: ~140 passengers")
    print("  Off-peak: 40-60 passengers")

# -----------------------------
# DEMAND MODEL 5: REALISTIC (with randomness)
# -----------------------------
elif DEMAND_MODEL == "REALISTIC":
    # Most realistic: combines multiple factors + random variation
    
    airport_multipliers = {
        1: 1.4,   # Arlanda (largest)
        2: 1.2,   # Kastrup
        3: 1.0    # Gardermoen
    }
    
    # Day-of-week effect (if you extend to weekly planning)
    # weekday_multiplier = 1.2  # More business travel
    # weekend_multiplier = 0.9  # More leisure travel
    
    np.random.seed(42)  # For reproducibility
    
    demand_out = {}
    for k in K_out:
        dep_time = D_k[k]
        dep_hour = dep_time / 60
        airport = flight_station_out[k]
        
        # Base demand by time
        if 6 <= dep_hour < 9:
            base = 180  # Morning peak (business)
        elif 17 <= dep_hour < 20:
            base = 160  # Evening peak
        elif 9 <= dep_hour < 17:
            base = 110  # Midday
        elif 20 <= dep_hour < 23:
            base = 70   # Evening
        else:
            base = 30   # Very early/late
        
        # Apply airport multiplier
        base *= airport_multipliers[airport]
        
        # Add random variation (±20%)
        variation = np.random.uniform(0.8, 1.2)
        demand_out[k] = int(base * variation)
    
    demand_in = {}
    for m in K_in:
        arr_time = A_m[m]
        arr_hour = arr_time / 60
        airport = flight_station_in[m]
        
        if 6 <= arr_hour < 9:
            base = 180
        elif 17 <= arr_hour < 20:
            base = 160
        elif 9 <= arr_hour < 17:
            base = 110
        elif 20 <= arr_hour < 23:
            base = 70
        else:
            base = 30
        
        base *= airport_multipliers[airport]
        variation = np.random.uniform(0.8, 1.2)
        demand_in[m] = int(base * variation)
    
    print("Realistic demand with random variation:")
    print("  Morning peak: 140-250 passengers")
    print("  Evening peak: 120-220 passengers")
    print("  Midday: 80-150 passengers")
    print("  Off-peak: 20-80 passengers")

else:
    raise ValueError(f"Unknown DEMAND_MODEL: {DEMAND_MODEL}")

# -----------------------------
# Demand Statistics
# -----------------------------
print(f"\n{'='*70}")
print("DEMAND STATISTICS")
print(f"{'='*70}")
print(f"Outgoing flights:")
print(f"  Total demand: {sum(demand_out.values())} passengers")
print(f"  Average: {sum(demand_out.values())/len(demand_out):.1f} per flight")
print(f"  Range: {min(demand_out.values())}-{max(demand_out.values())}")

print(f"\nIncoming flights:")
print(f"  Total demand: {sum(demand_in.values())} passengers")
print(f"  Average: {sum(demand_in.values())/len(demand_in):.1f} per flight")
print(f"  Range: {min(demand_in.values())}-{max(demand_in.values())}")

print(f"\nTotal system demand: {sum(demand_out.values()) + sum(demand_in.values())} passengers")
print(f"{'='*70}\n")

# -----------------------------
# Identify High-Demand Flights (for optional service level constraints)
# -----------------------------
# Define "high demand" as top 30% of flights
demand_threshold_out = np.percentile(list(demand_out.values()), 70)
demand_threshold_in = np.percentile(list(demand_in.values()), 70)

high_demand_flights_out = [k for k in K_out if demand_out[k] >= demand_threshold_out]
high_demand_flights_in = [m for m in K_in if demand_in[m] >= demand_threshold_in]

print(f"High-demand flights (top 30%):")
print(f"  Outgoing: {len(high_demand_flights_out)} flights (demand ≥ {demand_threshold_out:.0f})")
print(f"  Incoming: {len(high_demand_flights_in)} flights (demand ≥ {demand_threshold_in:.0f})")
print(f"{'='*70}\n")

# -----------------------------
# Optional: Demand Sensitivity Parameter
# -----------------------------
# Controls how much demand affects prioritization
# alpha = 0: ignore demand (all flights equal)
# alpha = 1: full demand weighting
# alpha > 1: amplify demand differences
DEMAND_SENSITIVITY = 1.0

# Normalize demands if sensitivity != 1
if DEMAND_SENSITIVITY != 1.0:
    demand_out = {k: d ** DEMAND_SENSITIVITY for k, d in demand_out.items()}
    demand_in = {m: d ** DEMAND_SENSITIVITY for m, d in demand_in.items()}
    print(f"Demand sensitivity: {DEMAND_SENSITIVITY}")
    print(f"(Higher values amplify demand differences)\n")























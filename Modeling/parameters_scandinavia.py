# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 13:25:40 2026

@author: evert
"""

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











"""
FLight frequency lookup
"""

import pandas as pd

# --- Load data ---
OD_data = pd.read_csv("../Data/Flight Data/OD Data/merged_OD_data_EU_only.csv")
print("Airport data loaded. Total rows:", len(OD_data))
# --- Load airport names ---
airport_info = pd.read_csv("../Data/Flight Data/airport_locations_with_names.csv")

# Create dictionary: ICAO -> Name
icao_to_name = dict(zip(airport_info["ICAO"], airport_info["Airport_Name"]))

print("Airport names loaded:", len(icao_to_name))

# ------------------ Filter passenger data -------------------------------------------
# Keep only rows where tra_meas is exactly 'PAS_CRD' to avoid summing multiple measures
passengers_data = OD_data[OD_data['tra_meas'] == 'PAS_CRD'].copy()
print("Passenger rows (PAS_CRD only):", len(passengers_data))

# Convert OBS_VALUE to numeric and drop missing values
passengers_data['OBS_VALUE'] = pd.to_numeric(passengers_data['OBS_VALUE'], errors='coerce')
passengers_data = passengers_data.dropna(subset=['OBS_VALUE'])
print("Passenger rows after cleaning:", len(passengers_data))

# --- Keep only relevant columns ---
passengers_data = passengers_data[['airp_pr', 'OBS_VALUE']].copy()

# --- Convert airp_pr to readable OD pair ---
def convert_icao(icao_pair):
    parts = icao_pair.split('_')
    if len(parts) == 4:
        return f"{parts[1]} - {parts[3]}"
    else:
        return icao_pair  # fallback if unexpected format

passengers_data['OD_pair'] = passengers_data['airp_pr'].apply(convert_icao)

# --- Split OD_pair into separate columns ---
passengers_data[['Origin', 'Destination']] = passengers_data['OD_pair'].str.split(' - ', expand=True)

# --- Pivot to create OD matrix ---
OD_matrix_passengers = passengers_data.pivot_table(
    index='Origin',
    columns='Destination',
    values='OBS_VALUE',
    aggfunc='first',  # take the single value per OD pair
    fill_value=0
)

print(OD_matrix_passengers.head())

# --- Optional: save to CSV ---
OD_matrix_passengers.to_csv("../Data/Flight Data/OD Data/OD_matrix_passengers.csv")

print("OD matrix created. Shape:", OD_matrix_passengers.shape)

# --- Load flight data ---
OD_data_flights = pd.read_csv("../Data/Flight Data/OD Data/merged_OD_data_EU_only.csv")
print("Flight data loaded. Total rows:", len(OD_data_flights))

# --- Filter only flight rows ---
# Keep only rows where unit is 'FLIGHT' to get number of flights
flights_data = OD_data_flights[OD_data_flights['unit'] == 'FLIGHT'].copy()
print("Flight rows (unit == FLIGHT):", len(flights_data))

# Convert OBS_VALUE to numeric and drop missing values
flights_data['OBS_VALUE'] = pd.to_numeric(flights_data['OBS_VALUE'], errors='coerce')
flights_data = flights_data.dropna(subset=['OBS_VALUE'])
print("Flight rows after cleaning:", len(flights_data))

# --- Keep only relevant columns ---
flights_data = flights_data[['airp_pr', 'OBS_VALUE']].copy()

# --- Convert airp_pr to readable OD pair ---
def convert_icao(icao_pair):
    parts = icao_pair.split('_')
    if len(parts) == 4:
        return f"{parts[1]} - {parts[3]}"
    else:
        return icao_pair  # fallback if unexpected format

flights_data['OD_pair'] = flights_data['airp_pr'].apply(convert_icao)

# --- Split OD_pair into separate columns ---
flights_data[['Origin', 'Destination']] = flights_data['OD_pair'].str.split(' - ', expand=True)

# --- Pivot to create OD matrix ---
OD_matrix_flights = flights_data.pivot_table(
    index='Origin',
    columns='Destination',
    values='OBS_VALUE',
    aggfunc='first',  # take the single value per OD pair
    fill_value=0
)

print(OD_matrix_flights.head())

# --- Optional: save to CSV ---
OD_matrix_flights.to_csv("../Data/Flight Data/OD Data/OD_matrix_flights.csv")


def interactive_OD_lookup(OD_matrix):
    """
    Ask the user to type two ICAO codes and print passenger count + airport names.
    """
    while True:
        print("Passenger lookup")
        print("Type 'exit' at any time to quit and continue to flight frequency lookup.")
        
        origin = input("Enter origin ICAO code: ").strip().upper()
        if origin == 'EXIT':
            break
        
        destination = input("Enter destination ICAO code: ").strip().upper()
        if destination == 'EXIT':
            break
        
        try:
            passengers = int(OD_matrix.at[origin, destination])
            
            origin_name = icao_to_name.get(origin, "Unknown airport")
            destination_name = icao_to_name.get(destination, "Unknown airport")
            
            print(f"\nPassengers:")
            print(f"{origin} ({origin_name}) → {destination} ({destination_name})")
            print(f"Total passengers: {passengers}\n")
            
        except KeyError:
            print("One or both ICAO codes not found in the OD matrix. Please try again.\n")

# --- Run interactive lookup ---

interactive_OD_lookup(OD_matrix_passengers)

def interactive_OD_lookup_flights(OD_matrix):
    """
    Ask the user to type two ICAO codes and print flight count + airport names.
    """
    while True:
        print("Flight frequency lookup")
        print("Type 'exit' at any time to quit.")
        
        origin = input("Enter origin ICAO code: ").strip().upper()
        if origin == 'EXIT':
            break
        
        destination = input("Enter destination ICAO code: ").strip().upper()
        if destination == 'EXIT':
            break
        
        try:
            flights = int(OD_matrix.at[origin, destination])
            
            origin_name = icao_to_name.get(origin, "Unknown airport")
            destination_name = icao_to_name.get(destination, "Unknown airport")
            
            print(f"\nFlights:")
            print(f"{origin} ({origin_name}) → {destination} ({destination_name})")
            print(f"Total flights: {flights}")
            print("Average flights per day:", flights/365, "\n")
            
        except KeyError:
            print("One or both ICAO codes not found in the OD matrix. Please try again.\n")


# --- Run interactive lookup ---
print("")
interactive_OD_lookup_flights(OD_matrix_flights)





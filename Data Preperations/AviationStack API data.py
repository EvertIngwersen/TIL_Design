import requests
import pandas as pd
from pathlib import Path
from datetime import date

API_KEY = "a721752689a14e0b69d2f1f760fa4452"
BASE_URL = "http://api.aviationstack.com/v1/flights"

# Airports (IATA codes)
AIRPORTS = {
    "ARN": "Stockholm Arlanda",
    "CPH": "Copenhagen Kastrup",
    "OSL": "Oslo Gardermoen"
}

# Base folder relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
SAVE_DIR = SCRIPT_DIR / "../../Large Data"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

def get_flights(params):
    all_flights = []
    offset = 0
    limit = 100

    while True:
        params["offset"] = offset
        params["limit"] = limit

        response = requests.get(BASE_URL, params=params)
        data = response.json()

        # Stop if there is an error
        if "error" in data:
            print("API error:", data["error"]["message"])
            return []

        flights = data.get("data", [])
        all_flights.extend(flights)

        print(f"Downloaded {len(all_flights)} flights so far")

        if len(flights) < limit:
            break

        offset += limit

    return all_flights

def extract_data(flights):
    rows = []

    for f in flights:
        rows.append({
            "flight_date": f.get("flight_date"),
            "flight_number": f.get("flight", {}).get("iata"),
            "airline": f.get("airline", {}).get("name"),

            "dep_airport": f.get("departure", {}).get("iata"),
            "dep_scheduled": f.get("departure", {}).get("scheduled"),
            "dep_actual": f.get("departure", {}).get("actual"),

            "arr_airport": f.get("arrival", {}).get("iata"),
            "arr_scheduled": f.get("arrival", {}).get("scheduled"),
            "arr_actual": f.get("arrival", {}).get("actual"),
        })

    return pd.DataFrame(rows)

# ------------------------
# Loop over airports
# ------------------------
for airport in AIRPORTS:
    print(f"\nProcessing airport: {airport}")

    # Departures
    params_departures = {
        "access_key": API_KEY,
        "dep_iata": airport
    }
    departures = get_flights(params_departures)

    # Arrivals
    params_arrivals = {
        "access_key": API_KEY,
        "arr_iata": airport
    }
    arrivals = get_flights(params_arrivals)

    # Convert to DataFrame
    df_departures = extract_data(departures)
    df_arrivals = extract_data(arrivals)

    df_all = pd.concat([df_departures, df_arrivals])

    # Save CSV
    today_str = date.today().isoformat()
    filename = SAVE_DIR / f"{airport}_flights_{today_str}.csv"
    df_all.to_csv(filename, index=False)

    print("Saved:", filename)
    print("Total flights:", len(df_all))
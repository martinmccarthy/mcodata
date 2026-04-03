import requests
from datetime import datetime, time, timezone
from dotenv import load_dotenv
from urllib.parse import quote
import json
import os

def check_for_data():
    filename = f"flights_{datetime.now().strftime('%Y-%m-%d')}.json"
    return os.path.exists(filename)

def convert_time(t):
    t = t.replace("%3A", ":")
    dt = datetime.fromisoformat(t)
    dt = dt.replace(microsecond=0, tzinfo=timezone.utc)
    iso = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return quote(iso, safe='')

def parse_flight_data(flight):
    return {
        "departure_airport": flight["origin"]["name"],
        "departure_city": flight["origin"]["city"],
        "arrival_airport": flight["destination"]["name"],
        "arrival_city": flight["destination"]["city"],
        "departure_time": flight["scheduled_out"],
        "arrival_time": flight["estimated_in"]
    }

def store_flight_data():
    if(check_for_data()):
        print("Already collected for today, if reset is needed delete local file.")
        return
    
    load_dotenv()
    api_key = os.environ["AERO_API"]
    start_of_day =  convert_time(datetime.combine(datetime.now(), time.min).isoformat())
    end_of_day = convert_time(datetime.combine(datetime.now(), time.max).isoformat())

    airport_id = "KMCO"
    airport_query = f"https://aeroapi.flightaware.com/aeroapi/airports/{airport_id}/flights?start={start_of_day}&end={end_of_day}&max_pages=10"

    API = requests.Session()
    API.headers.update({"x-apikey": api_key})

    data = API.get(airport_query).json()
    arrivals = data["arrivals"]
    departures = data["departures"]

    flights = []
    for flight in arrivals:
        flights.append(parse_flight_data(flight))

    for flight in departures:
        flights.append(parse_flight_data(flight))
        
    filename = f"flights_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(flights, f, indent=4)


store_flight_data()
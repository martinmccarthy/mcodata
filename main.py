import requests
from datetime import datetime, time, timezone
from dotenv import load_dotenv
from urllib.parse import quote
import json
import os
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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
        "id": flight["ident_iata"],
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


def retrieve_flight_data(**filters):
    filename = f"flights_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(filename, 'r') as f:
        data = json.load(f)
    results = [
        flight for flight in data
        if all(flight.get(k) == v for k, v in filters.items())
    ]
    return results if results else None

def get_completion(messages, model="gpt-4o-mini", temperature=0, max_tokens=300, tools=None):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        tools=tools
    )
    return response.choices[0].message

def query_flights(message):
    # we really should never do this, run a script thatll collect this data beforehand as itll take time to populate the flight
    # info, delaying a response
    if not check_for_data():
        store_flight_data()

    messages = [
        {
            "role": "user",
            "content": message
        }
    ]

    tools = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_flight_data",
            "description": "Search for flights matching any combination of flight fields. Returns all matching flights.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The Flight ID, e.g. DL1705"
                    },
                    "departure_airport": {
                        "type": "string",
                        "description": "Full name of the departure airport"
                    },
                    "departure_city": {
                        "type": "string",
                        "description": "City of departure"
                    },
                    "arrival_airport": {
                        "type": "string",
                        "description": "Full name of the arrival airport"
                    },
                    "arrival_city": {
                        "type": "string",
                        "description": "City of arrival"
                    },
                    "departure_time": {
                        "type": "string",
                        "description": "Scheduled departure time (ISO 8601)"
                    },
                    "arrival_time": {
                        "type": "string",
                        "description": "Estimated arrival time (ISO 8601)"
                    }
                },
                "required": []
            }
        }
    }]

    response = get_completion(messages, tools=tools)

    if response.tool_calls:
        for call in response.tool_calls:
            args = json.loads(call.function.arguments)
            info = retrieve_flight_data(**args)
            return info
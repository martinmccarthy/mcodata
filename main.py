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


def retrieve_flight_data(flight_id):
    filename = f"flights_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(filename, 'r') as f:
        data = json.load(f)
        for i in data:
            if i['id'] == flight_id:
                return i
        
    return None
# store_flight_data()


tools = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_flight_data",
            "description": "Get the information from the JSON file based on this flight ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The Flight ID, e.g. DL1705"
                    },
                },
                "required": ["id"]
            }
        }
    }
]

def get_completion(messages, model="gpt-3.5-turbo-1106", temperature=0, max_tokens=300, tools=None):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        tools=tools
    )
    return response.choices[0].message

x = input()

messages = [
    {
        "role": "user",
        "content": x
    }
]

response = get_completion(messages, tools=tools)

if response.tool_calls:
    for call in response.tool_calls:
        print("Tool:", call.function.name)
        print("Args:", call.function.arguments)
        args = json.loads(call.function.arguments)
        info = retrieve_flight_data(args["id"])
        print(info)
else:
    print(response.content)


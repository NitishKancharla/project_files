import requests
from dotenv import load_dotenv
import os

load_dotenv()

class FlightSearchAgent:
    def __init__(self):
        self.api_key = os.getenv("SKYSCANNER_API_KEY")
        self.headers = {
            "x-rapidapi-host": "skyscanner89.p.rapidapi.com",
            "x-rapidapi-key": self.api_key
        }

    def search_flights(self, state):
        destination = state.get("destination")
        start_date = state.get("start_date")
        
        # Mocked API call (simplified)
        url = "https://skyscanner89.p.rapidapi.com/flights/roundtrip/list"
        params = {
            "origin": "NYCA",
            "destination": "HNL",  # Map destination to code
            "originId": "27537542",
            "destinationId": "95673827"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            flights = response.json()
            state["flights"] = {"options": flights.get("results", []), "estimated_cost": 500}  # Mocked cost
        except Exception as e:
            state["flights"] = {"error": str(e)}
        
        return state
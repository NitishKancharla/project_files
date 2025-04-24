import requests
from dotenv import load_dotenv
import os

load_dotenv()

class HotelSearchAgent:
    def __init__(self):
        self.api_key = os.getenv("SKYSCANNER_API_KEY")
        self.headers = {
            "x-rapidapi-host": "skyscanner89.p.rapidapi.com",
            "x-rapidapi-key": self.api_key
        }

    def search_hotels(self, state):
        destination = state.get("destination")
        budget = state.get("budget")
        
        # Mocked API call
        url = "https://skyscanner89.p.rapidapi.com/hotels/list"
        params = {"entity_id": "27537542"}  # Mocked entity ID
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            hotels = response.json()
            state["hotels"] = {"options": hotels.get("results", []), "estimated_cost": 200 * 5}  # Mocked for 5 nights
        except Exception as e:
            state["hotels"] = {"error": str(e)}
        
        return state
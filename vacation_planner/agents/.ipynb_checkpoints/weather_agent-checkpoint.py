import requests
from dotenv import load_dotenv
import os

load_dotenv()

class WeatherAgent:
    def __init__(self):
        self.api_key = os.getenv("WEATHER_API_KEY")

    def get_weather(self, state):
        destination = state.get("destination")
        start_date = state.get("start_date")
        
        url = "http://api.weatherapi.com/v1/forecast.json"
        params = {
            "key": self.api_key,
            "q": destination,
            "days": 7
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            weather = response.json()
            state["weather"] = weather.get("forecast", {}).get("forecastday", [])
        except Exception as e:
            state["weather"] = {"error": str(e)}
        
        return state
from vacation_planner.agents.base_agent import BaseAgent
from vacation_planner.core.gemini_client import GeminiHelper
from .base_agent import BaseAgent
import requests
from datetime import datetime

class WeatherAgent(BaseAgent):
    def run(self, state):
        try:
            destination = state['destination']
            start_date = state['dates'][0]
            end_date = state['dates'][1]
            
            response = requests.get(
                f"http://api.weatherapi.com/v1/forecast.json",
                params={
                    "key": os.getenv("WEATHER_API_KEY"),
                    "q": destination,
                    "days": (end_date - start_date).days,
                    "aqi": "no",
                    "alerts": "no"
                }
            )
            
            forecast = response.json()['forecast']['forecastday']
            return {**state, 'weather': forecast}
            
        except Exception as e:
            print(f"Weather error: {e}")
            return {**state, 'weather': {}}
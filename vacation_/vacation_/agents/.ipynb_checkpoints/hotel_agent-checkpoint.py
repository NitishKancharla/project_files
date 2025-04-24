from vacation_planner.agents.base_agent import BaseAgent
from vacation_planner.core.gemini_client import GeminiHelper
from .base_agent import BaseAgent
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class HotelSearchAgent(BaseAgent):
    def run(self, state):
        try:
            destination = state['destination']
            checkin = state['dates'][0]
            checkout = state['dates'][1]
            budget = state['budget_level']
            
            # Connect to Booking.com API
            headers = {
                "X-RapidAPI-Key": os.getenv("BOOKING_API_KEY"),
                "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
            }
            
            params = {
                "checkin_date": checkin,
                "dest_type": "city",
                "units": "metric",
                "checkout_date": checkout,
                "adults_number": "2",
                "order_by": "price",
                "dest_id": self._get_destination_id(destination),
                "filter_by_currency": "USD",
                "room_number": "1",
                "price_filter_currency": "USD"
            }

            response = requests.get(
                "https://booking-com.p.rapidapi.com/v1/hotels/search",
                headers=headers,
                params=params
            )

            hotels = sorted(response.json()['result'], key=lambda x: x['price'])[:3]
            return {**state, 'hotels': hotels}
            
        except Exception as e:
            print(f"Hotel search error: {e}")
            return {**state, 'hotels': []}

    def _get_destination_id(self, destination):
        # Implement location to ID mapping
        return "-1456928"  # Example: Paris ID
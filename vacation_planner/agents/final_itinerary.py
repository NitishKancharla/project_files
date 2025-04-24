import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class FinalItineraryAgent:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def compile_itinerary(self, state):
        prompt = f"""
        Compile a final vacation itinerary using:
        - Destination: {state.get('destination')}
        - Dates: {state.get('start_date')} to {state.get('end_date')}
        - Interests: {', '.join(state.get('interests', []))}
        - Budget: {state.get('budget')}
        - Flights: {state.get('flights')}
        - Hotels: {state.get('hotels')}
        - Itinerary: {state.get('itinerary')}
        - Restaurants: {state.get('restaurants')}
        - Weather: {state.get('weather')}
        - Budget Estimate: {state.get('budget_estimate')}
        
        Format as a detailed, readable summary.
        """
        response = self.model.generate_content(prompt)
        
        state["final_itinerary"] = response.text
        return state
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class AttractionsPlannerAgent:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def plan_attractions(self, state):
        destination = state.get("destination")
        interests = state.get("interests")
        start_date = state.get("start_date")
        end_date = state.get("end_date")
        
        prompt = f"""
        Create a day-by-day itinerary for a trip to {destination} from {start_date} to {end_date}.
        Focus on {', '.join(interests)}. Include 2-3 activities per day.
        """
        response = self.model.generate_content(prompt)
        
        state["itinerary"] = response.text
        return state
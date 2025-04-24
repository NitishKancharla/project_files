import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class FoodAgent:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def find_restaurants(self, state):
        destination = state.get("destination")
        budget = state.get("budget")
        
        prompt = f"Recommend top restaurants in {destination} suitable for a {budget} budget."
        response = self.model.generate_content(prompt)
        
        state["restaurants"] = response.text
        return state
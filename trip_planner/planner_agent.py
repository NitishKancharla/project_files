import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM"))

def generate_itinerary(location: str, days: int) -> str:
    prompt = f"""
    Create a detailed {days}-day travel itinerary for {location}. 
    Include:
    - Morning, afternoon, and evening activities
    - Tourist spots
    - Food suggestions
    - Cultural/local experiences
    Format clearly with Day 1, Day 2, etc.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

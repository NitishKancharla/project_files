import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM"))

def find_attractions(location: str):
    prompt = f"List the top 5 tourist attractions in {location}. Only list their names in bullet points."
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    lines = response.text.strip().split("\n")
    return [line.strip("-• ").strip() for line in lines if line.strip()]

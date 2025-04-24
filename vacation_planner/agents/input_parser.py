import google.generativeai as genai
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class InputParserAgent:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def parse_input(self, state):
        user_input = state.get("user_input", {})
        prompt = f"""
        Parse and validate the following user input for a vacation planner:
        Destination: {user_input.get('destination', '')}
        Dates: {user_input.get('dates', [])}
        Interests: {user_input.get('interests', [])}
        Budget: {user_input.get('budget', '')}
        
        Ensure:
        - Destination is a valid city name.
        - Dates are in the future and include start/end.
        - Interests are from [Nature, Museums, Food, Shopping, Adventure].
        - Budget is Low, Medium, or High.
        
        Return a JSON with parsed data or errors.
        """
        response = self.model.generate_content(prompt)
        parsed = eval(response.text.strip("```python\n").strip("\n```"))
        
        if "errors" in parsed:
            return {"errors": parsed["errors"]}
        
        state["parsed_input"] = parsed
        state["destination"] = parsed["destination"]
        state["start_date"] = parsed["start_date"]
        state["end_date"] = parsed["end_date"]
        state["interests"] = parsed["interests"]
        state["budget"] = parsed["budget"]
        return state
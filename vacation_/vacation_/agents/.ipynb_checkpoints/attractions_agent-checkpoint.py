from core.gemini_client import GeminiHelper
from .base_agent import BaseAgent
from vacation_planner.agents.base_agent import BaseAgent
from vacation_planner.core.gemini_client import GeminiHelper
class AttractionsPlannerAgent(BaseAgent):
    def run(self, state):
        gemini = GeminiHelper()
        prompt = f"""
        Create a {state['duration_days']}-day itinerary for {state['destination']} 
        focusing on: {', '.join(state['interests']}.
        Include specific attractions, time allocations, and brief descriptions.
        Format as JSON with keys: day_number, morning, afternoon, evening.
        """
        
        response = gemini.generate(
            system_message="You are an expert travel planner. Return valid JSON only.",
            prompt=prompt
        )
        
        state['itinerary'] = self._parse_response(response)
        return state

    def _parse_response(self, response):
        # Add JSON parsing logic here
        import json
        return json.loads(response)
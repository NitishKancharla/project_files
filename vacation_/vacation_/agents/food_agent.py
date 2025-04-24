from vacation_planner.agents.base_agent import BaseAgent
from vacation_planner.core.gemini_client import GeminiHelper
from .base_agent import BaseAgent
from core.gemini_client import GeminiHelper

class FoodAgent(BaseAgent):
    def run(self, state):
        gemini = GeminiHelper()
        prompt = f"""
        Suggest 3-5 restaurants in {state['destination']} matching these criteria:
        - Budget level: {state['budget']}
        - Cuisine preferences: {', '.join(state.get('food_preferences', []))}
        - Dietary restrictions: {', '.join(state.get('dietary_restrictions', []))}
        
        Include name, address, price range, and specialty dish.
        Format as JSON list with restaurant details.
        """
        
        response = gemini.generate(
            system_message="You are a local food expert. Return valid JSON only.",
            prompt=prompt
        )
        
        state['restaurants'] = self._parse_response(response)
        return state
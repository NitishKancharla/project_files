from vacation_planner.agents.base_agent import BaseAgent
from vacation_planner.core.gemini_client import GeminiHelper
from .base_agent import BaseAgent
class BudgetEstimatorAgent(BaseAgent):
    def run(self, state):
        from smol_developer import AutoCoder
        
        coder = AutoCoder()
        code = coder.generate_code(
            prompt="Calculate total vacation cost",
            context=f"""
            Flights: {state['flights'][0]['price']}
            Hotels: {sum(h['price'] for h in state['hotels'])}
            Activities: {len(state['itinerary']) * 50}
            Food: {len(state['restaurants']) * 30}
            """
        )
        
        total_cost = eval(code)
        return {**state, 'total_cost': total_cost}
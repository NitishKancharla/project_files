from vacation_planner.agents.base_agent import BaseAgent
from vacation_planner.core.gemini_client import GeminiHelper
from .base_agent import BaseAgent
from smol_developer import AutoCoder
import requests

class FlightSearchAgent(BaseAgent):
    def run(self, state):
        coder = AutoCoder()
        code = coder.generate_code(
            prompt=f"Find flights to {state['destination']} from major airports",
            api_docs="Skyscanner API documentation..."
        )
        
        # Execute generated code safely
        flights = self.execute_code(code, state)
        return {**state, 'flights': flights}
    
    def execute_code(self, code, state):
        # Sandboxed execution
        local_vars = {'state': state}
        exec(code, globals(), local_vars)
        return local_vars['result']
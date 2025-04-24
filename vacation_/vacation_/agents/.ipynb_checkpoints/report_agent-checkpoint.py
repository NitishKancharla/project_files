from vacation_planner.agents.base_agent import BaseAgent
from vacation_planner.core.gemini_client import GeminiHelper
from .base_agent import BaseAgent
from weasyprint import HTML
import tempfile

class ReportAgent(BaseAgent):
    def run(self, state):
        html_content = self._generate_html(state)
        pdf_content = self._create_pdf(html_content)
        return {**state, 'report': html_content, 'pdf': pdf_content}

    def _generate_html(self, state):
        return f"""
        <html>
            <head><style>
                body {{ font-family: Arial; margin: 2em; }}
                .header {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
                .day {{ margin: 1em 0; padding: 1em; background: #f9f9f9; }}
                .weather {{ color: #2980b9; }}
            </style></head>
            <body>
                <h1 class="header">{state['destination']} Itinerary</h1>
                <p>Dates: {state['dates'][0]} to {state['dates'][1]}</p>
                <h3>Total Estimated Cost: ${state['total_cost']}</h3>
                
                {"".join(self._format_day(day) for day in state['itinerary'])}
                
                <h2>Recommended Restaurants</h2>
                <ul>
                    {"".join(f"<li>{r['name']} ({r['cuisine']}) - {r['price']}</li>" 
                    for r in state['restaurants'])}
                </ul>
            </body>
        </html>
        """

    def _format_day(self, day_data):
        return f"""
        <div class="day">
            <h3>Day {day_data['day']}</h3>
            <p class="weather">Weather: {day_data['weather']}</p>
            <ul>
                {"".join(f"<li>{activity}</li>" for activity in day_data['activities'])}
            </ul>
        </div>
        """

    def _create_pdf(self, html):
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
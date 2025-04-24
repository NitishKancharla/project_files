from typing import Dict


class ReportAgent:
    def generate(self, state: Dict) -> Dict:
        itinerary = state.get("itinerary", {})
        
        try:
            flights = itinerary.get("flights", [])
            hotels = itinerary.get("hotels", [])
            attractions = itinerary.get("attractions", [])
            restaurants = itinerary.get("restaurants", [])
            weather = itinerary.get("weather", {}).get("forecast", [])
            
            html_content = f"""
            <h1>Itinerary for {itinerary.get('destination', 'Unknown')}</h1>
            <h2>Dates</h2>
            <p>{itinerary.get('dates', {}).get('start', '')} to \
{itinerary.get('dates', {}).get('end', '')}</p>
            <h2>Flights</h2>
            <ul>
            {''.join(f'<li>{f["airline"]} - ${f["price"]}</li>'
                     for f in flights
                     if isinstance(f, dict) and "airline" in f)}
            </ul>
            <h2>Hotels</h2>
            <ul>
            {''.join(f'<li>{h["name"]} - ${h["price_per_night"]}/night</li>'
                     for h in hotels
                     if isinstance(h, dict) and "name" in h)}
            </ul>
            <h2>Attractions</h2>
            <ul>
            {''.join(f'<li>Day {a["day"]}: {a["activity"]}</li>'
                     for a in attractions
                     if isinstance(a, dict) and "day" in a)}
            </ul>
            <h2>Restaurants</h2>
            <ul>
            {''.join(f'<li>{r["name"]} ({r["cuisine"]})</li>'
                     for r in restaurants
                     if isinstance(r, dict) and "name" in r)}
            </ul>
            <h2>Weather</h2>
            <ul>
            {''.join(f'<li>{w["day"]}: {w["condition"]}, {w["temp"]}°C</li>'
                     for w in weather
                     if isinstance(w, dict) and "day" in w)}
            </ul>
            <h2>Budget</h2>
            <p>Total: ${itinerary.get('budget', {}).get('total', 0)}</p>
            """
            state["report"] = html_content
        except Exception as e:
            state["report"] = f"Report generation failed: {str(e)}"
        
        return state
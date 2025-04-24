from langgraph.graph import StateGraph
from agents.input_parser import InputParserAgent
from agents.info_retriever import InfoRetrieverAgent
from agents.flight_search import FlightSearchAgent
from agents.hotel_search import HotelSearchAgent
from agents.attractions_planner import AttractionsPlannerAgent
from agents.food_agent import FoodAgent
from agents.weather_agent import WeatherAgent
from agents.budget_estimator import BudgetEstimatorAgent
from agents.final_itinerary import FinalItineraryAgent
from typing import Dict, Any

# Define the state schema
State = Dict[str, Any]

def create_graph():
    graph = StateGraph(state_schema=State)
    
    # Add nodes
    graph.add_node("parser", InputParserAgent().parse_input)
    graph.add_node("retriever", InfoRetrieverAgent().retrieve_info)
    graph.add_node("flights", FlightSearchAgent().search_flights)
    graph.add_node("hotels", HotelSearchAgent().search_hotels)
    graph.add_node("attractions", AttractionsPlannerAgent().plan_attractions)
    graph.add_node("food", FoodAgent().find_restaurants)
    graph.add_node("weather", WeatherAgent().get_weather)
    graph.add_node("budget", BudgetEstimatorAgent().estimate_budget)
    graph.add_node("final", FinalItineraryAgent().compile_itinerary)
    
    # Set entry point
    graph.set_entry_point("parser")
    
    # Add edges
    graph.add_edge("parser", "retriever")
    graph.add_edge("retriever", "flights")
    graph.add_edge("flights", "hotels")
    graph.add_edge("hotels", "attractions")
    graph.add_edge("attractions", "food")
    graph.add_edge("food", "weather")
    graph.add_edge("weather", "budget")
    graph.add_edge("budget", "final")
    
    # Return the graph without compiling (temporary workaround)
    return graph
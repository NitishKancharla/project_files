from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from planner_agent import generate_itinerary
from agents.gemini_search import find_attractions
from agents.hotel_booking import book_hotel

# Define the state schema for the trip
class TripState(TypedDict):
    location: str
    days: int
    group_size: int
    itinerary: str
    attractions: List[str]
    hotel_status: str
    alert_status: bool

# Nodes for each task in the flow
def planner_node(state: TripState) -> TripState:
    # Generate itinerary based on location and days
    itinerary = generate_itinerary(state["location"], state["days"])
    return {**state, "itinerary": itinerary}

def attractions_node(state: TripState) -> TripState:
    # Find attractions based on location
    attractions = find_attractions(state["location"])
    return {**state, "attractions": attractions}

def hotel_node(state: TripState) -> TripState:
    # Simulate hotel booking
    hotel_status = book_hotel(state["location"], state["group_size"])
    return {**state, "hotel_status": hotel_status}

# Main function to build and return the flow graph
def build_flow():
    graph = StateGraph(TripState)
    
    # Add nodes in the required order
    graph.add_node("Planner", planner_node)
    graph.add_node("Attractions", attractions_node)
    graph.add_node("BookHotel", hotel_node)

    # Set the entry point and define the order of execution
    graph.set_entry_point("Planner")
    graph.add_edge("Planner", "Attractions")
    graph.add_edge("Attractions", "BookHotel")
    graph.add_edge("BookHotel", END)

    return graph.compile()

from langgraph.graph import StateGraph, END
from typing import TypedDict, Any

class PlannerState(TypedDict):
    destination: str
    dates: tuple
    preferences: list
    budget: str
    flights: list
    hotels: list
    attractions: list
    restaurants: list
    weather: dict
    total_cost: float

def build_agent_workflow():
    # Import agents inside function to break cycle
    from vacation_planner.agents import (
        InputParserAgent,
        InfoRetrieverAgent,
        FlightSearchAgent,
        HotelSearchAgent,
        AttractionsPlannerAgent,
        FoodAgent,
        WeatherAgent,
        BudgetEstimatorAgent,
        ReportAgent
    )

    graph = StateGraph(PlannerState)
    
    # Add nodes
    graph.add_node("input_parser", InputParserAgent().run)
    graph.add_node("info_retriever", InfoRetrieverAgent().run)
    # ... add other nodes ...
    graph.add_node("flight_finder", flight_finder.run)
    graph.add_node("hotel_finder", hotel_finder.run)
    graph.add_node("attractions_planner", attractions_planner.run)
    graph.add_node("restaurant_finder", restaurant_finder.run)
    graph.add_node("weather_checker", weather_checker.run)
    graph.add_node("budget_calculator", budget_calculator.run)
    graph.add_node("report_generator", report_generator.run)

    # Define execution flow
    graph.set_entry_point("input_parser")
    graph.add_edge("input_parser", "info_retriever")
    graph.add_edge("info_retriever", "flight_finder")
    graph.add_edge("flight_finder", "hotel_finder")
    graph.add_edge("hotel_finder", "attractions_planner")
    graph.add_edge("attractions_planner", "restaurant_finder")
    graph.add_edge("restaurant_finder", "weather_checker")
    graph.add_edge("weather_checker", "budget_calculator")
    graph.add_edge("budget_calculator", "report_generator")
    graph.add_edge("report_generator", END)

    return graph.compile()

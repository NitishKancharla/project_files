import streamlit as st
from graph import create_graph
from datetime import datetime
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="AI Vacation Planner", layout="wide")

st.title("AI Vacation Planner 🧳")

# Input form
with st.form("vacation_form"):
    destination = st.text_input("Where do you want to go?", "Paris")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", min_value=datetime.today())
    with col2:
        end_date = st.date_input("End Date", min_value=start_date)
    interests = st.multiselect("Your Interests", ["Nature", "Museums", "Food", "Shopping", "Adventure"], default=["Museums", "Food"])
    budget = st.radio("Your Budget", ["Low", "Medium", "High"], index=1)
    submit = st.form_submit_button("Plan My Trip")

if submit:
    # Initialize LangGraph
    graph = create_graph()
    
    # Prepare input
    state = {
        "user_input": {
            "destination": destination,
            "dates": [start_date, end_date],
            "interests": interests,
            "budget": budget
        }
    }
    
    # Manually invoke nodes (fixed for PregelNode)
    with st.spinner("Planning your dream vacation..."):
        nodes = ["parser", "retriever", "flights", "hotels", "attractions", "food", "weather", "budget", "final"]
        for node in nodes:
            node_func = graph.nodes[node].func  # Access the callable function
            state = node_func(state)
    
    # Display results
    if "errors" in state:
        st.error(f"Input Error: {state['errors']}")
    else:
        st.success("Here's your itinerary!")
        
        # Itinerary
        st.subheader("Your Vacation Plan")
        st.markdown(state["final_itinerary"])
        
        # Budget Breakdown
        budget_data = state.get("budget_estimate", {})
        if budget_data:
            st.subheader("Budget Overview")
            df = pd.DataFrame({
                "Category": ["Flights", "Hotels", "Food", "Total"],
                "Cost ($)": [
                    budget_data.get("flights", 0),
                    budget_data.get("hotels", 0),
                    budget_data.get("food", 0),
                    budget_data.get("total", 0)
                ]
            })
            fig = px.pie(df, values="Cost ($)", names="Category", title="Budget Breakdown")
            st.plotly_chart(fig)
        
        # Map (mocked coordinates)
        st.subheader("Destination Map")
        m = folium.Map(location=[48.8566, 2.3522], zoom_start=12)  # Paris coordinates
        folium.Marker([48.8566, 2.3522], popup=destination).add_to(m)
        st_folium(m, width=700, height=400)
        
        # Weather (simplified)
        weather = state.get("weather", [])
        if weather and not isinstance(weather, dict):
            st.subheader("Weather Forecast")
            for day in weather[:3]:  # Show first 3 days
                st.write(f"{day['date']}: {day['day']['condition']['text']}, {day['day']['avgtemp_c']}°C")
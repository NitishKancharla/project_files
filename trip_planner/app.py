import streamlit as st
from agents.langgraph_flow import build_flow
from agents.hotel_booking import get_hotel_pricing, book_hotel

# Configure Streamlit page
st.set_page_config(page_title="🌍 AI Travel Assistant", layout="wide")
st.title("🧠 Agentic AI Vacation Planner")

# Inputs from user
location = st.text_input("📍 Destination", "Paris")
days = st.slider("🗓️ Duration (Days)", 1, 14, 5)
group_size = st.slider("👥 Group Size", 1, 10, 1)

# Feature for real-time alerts (weather, etc.)
alert_checkbox = st.checkbox("Enable Real-Time Alerts (Weather, Flight, Hotel Status)", value=True)

if st.button("🚀 Plan My Trip"):
    with st.spinner("Assembling agents, booking hotels..."):
        # Build and invoke the agent flow
        flow = build_flow()
        result = flow.invoke({
            "location": location,
            "days": days,
            "group_size": group_size,
            "itinerary": "",
            "attractions": [],
            "hotel_status": "",
            "alert_status": alert_checkbox
        })

        st.success("✅ Trip successfully planned!")

        # Display itinerary
        st.subheader("📅 Itinerary")
        st.markdown(result["itinerary"])

        # Display attractions
        st.subheader("📍 Attractions")
        for i, place in enumerate(result["attractions"], 1):
            st.markdown(f"{i}. {place}")

        # Display hotel booking status
        st.subheader("🏨 Hotel Booking")
        st.markdown(result["hotel_status"])

        # Enable alerts if selected
        if result["alert_status"]:
            st.subheader("⚠️ Real-Time Alerts")
            st.markdown("Weather alerts, flight delays, and hotel status will be sent directly to your phone.")


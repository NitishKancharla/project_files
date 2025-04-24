import streamlit as st
from vacation_planner.core.graph import build_agent_workflow

def main():
    st.set_page_config(page_title="AI Vacation Planner", layout="wide")
    
    st.title("🌍 AI-Powered Vacation Planner")
    
    with st.form("user_inputs"):
        col1, col2 = st.columns(2)
        destination = col1.text_input("Destination")
        dates = col2.date_input("Travel Dates", [])
        budget = st.selectbox("Budget Level", ["Low", "Medium", "High"])
        interests = st.multiselect("Interests", ["Beaches", "Hiking", "Museums", "Food", "Luxury"])
        
        if st.form_submit_button("Plan My Trip"):
            workflow = build_agent_workflow()
            result = workflow.invoke({
                "destination": destination,
                "dates": dates,
                "budget": budget,
                "interests": interests
            })
            
            display_results(result)

def display_results(result):
    st.header(f"✨ {result['destination']} Itinerary")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💰 Total Estimated Cost")
        st.metric(label="", value=f"${result['total_cost']}")
        
    with col2:
        st.subheader("☀️ Weather Overview")
        for day in result['weather']:
            st.write(f"{day['date']}: {day['day']['condition']['text']}")
    
    st.subheader("✈️ Top Flight Options")
    for flight in result['flights'][:3]:
        st.write(f"{flight['airline']} - ${flight['price']} - {flight['departure']} → {flight['arrival']}")
    
    st.subheader("🏨 Hotel Recommendations")
    for hotel in result['hotels'][:3]:
        st.write(f"{hotel['name']} - ${hotel['price']}/night - Rating: {hotel['rating']}")
    
    st.subheader("🗓 Daily Itinerary")
    for day in result['itinerary']:
        with st.expander(f"Day {day['day']} - {day['weather']}"):
            st.write("**Activities:**")
            for activity in day['activities']:
                st.write(f"- {activity}")
    
    st.download_button("📥 Download PDF Report", 
                      data=result['pdf'],
                      file_name="vacation_plan.pdf")

if __name__ == "__main__":
    main()
import streamlit as st
from pytrends.request import TrendReq
import google.generativeai as genai

# Configure Google Generative AI API
genai.configure(api_key="AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM")
model = genai.GenerativeModel("gemini-1.5-flash")

# Function to fetch trending topics from Google Trends
def fetch_trending_topics():
    pytrends = TrendReq(hl='en-US', tz=330)
    trending_searches_df = pytrends.trending_searches(pn='india')
    trending_topics = trending_searches_df[0].tolist()
    return trending_topics[:10]  # Get top 10 trending topics

# Function to generate Tenglish meme using Gemini API
def generate_tenglish_meme(topic):
    prompt = f"""
    Generate a humorous meme caption in Tenglish (Telugu + English) about "{topic}".
    The caption should be a blend of Telugu and English, reflecting casual conversation among friends.
    Example: "Weekend ki plans enti ra? Netflix and chill ha?"
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error generating meme: {e}")
        return ""

# Streamlit UI
st.set_page_config(page_title="Tenglish Meme Bot", layout="centered")
st.title("😂 Tenglish Meme Bot")

menu = st.sidebar.radio("Menu", ["Generate Meme", "Trending Topics", "Chat", "Exit"])

if menu == "Generate Meme":
    st.subheader("Generate a Tenglish Meme")
    topic = st.text_input("Enter a topic for the meme:")
    if st.button("Generate"):
        if topic:
            meme = generate_tenglish_meme(topic)
            st.success(f"Here's your meme: {meme}")
        else:
            st.warning("Please enter a topic.")

elif menu == "Trending Topics":
    st.subheader("Trending Topics")
    if st.button("Fetch Trending Topics"):
        trending_topics = fetch_trending_topics()
        if trending_topics:
            st.write("Top Trending Topics:")
            for i, topic in enumerate(trending_topics, 1):
                st.write(f"{i}. {topic}")
            selected_topic = st.selectbox("Select a topic to generate a meme:", trending_topics)
            if st.button("Generate Meme for Selected Topic"):
                meme = generate_tenglish_meme(selected_topic)
                st.success(f"Here's your meme: {meme}")
        else:
            st.warning("No trending topics found.")

elif menu == "Chat":
    st.subheader("Fun Chat")
    user_input = st.text_input("Say something:")
    if st.button("Reply"):
        prompt = f"""
        Respond humorously in Tenglish to: "{user_input}"
        """
        try:
            response = model.generate_content(prompt)
            st.success(response.text.strip())
        except Exception as e:
            st.error(f"Error generating reply: {e}")

elif menu == "Exit":
    st.write("Thank you for using the Tenglish Meme Bot!")


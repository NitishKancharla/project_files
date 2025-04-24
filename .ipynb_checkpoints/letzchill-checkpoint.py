import streamlit as st
import feedparser
import google.generativeai as genai
import random

# ================================
# Gemini API Setup
# ================================
genai.configure(api_key="AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM")
model = genai.GenerativeModel("gemini-1.5-flash")

# ================================
# Trending Topics from Google Trends (RSS Feed)
# ================================
def fetch_trending_topics():
    url = 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN'
    feed = feedparser.parse(url)
    topics = [entry['title'] for entry in feed.entries]
    return topics[:10]  # Top 10 topics

# ================================
# Generate Tenglish Meme Text
# ================================
def generate_tenglish_meme(context):
    prompt = f"""
    Generate a funny meme dialogue in Tenglish (Telugu + English mix) based on the topic: "{context}".
    Make it sound like a Hyderabadi friend's casual joke.
    
    Example style:
    "Orey bro, Elon Musk Twitter ni teesukunnaadu ra... mana tweet lu baapam orphan aipoyayi!"

    Keep the meme under 2 lines, very casual and funny.
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Error generating meme: {e}"

# ================================
# Streamlit App Interface
# ================================
st.set_page_config(page_title="😂 Tenglish Meme Bot", layout="centered")

st.title("😂 Tenglish Meme Bot")
st.markdown("Generate funny Hyderabadi-style memes from trending topics!\n\n_Uses Gemini 1.5 Flash + Google Trends RSS Feed_")

# Get Trending Topics
with st.spinner("Fetching trending topics..."):
    trending_topics = fetch_trending_topics()

if trending_topics:
    selected_topic = st.selectbox("📈 Choose a Trending Topic:", trending_topics)

    if st.button("🔥 Generate Meme"):
        with st.spinner("Generating meme with Gemini 1.5 Flash..."):
            meme = generate_tenglish_meme(selected_topic)
            st.success("Here’s your Tenglish meme! 😂")
            st.markdown(f"**💬 {meme}**")

else:
    st.error("Failed to fetch trending topics. Try again later.")

# Footer
st.markdown("---")
st.caption("Built with ❤️ using Gemini 1.5 Flash and Streamlit.")

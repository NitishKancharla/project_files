import streamlit as st
import requests
import google.generativeai as genai
import random

# --- API KEYS ---
GEMINI_API_KEY = "AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM"
NEWSDATA_API_KEY = "pub_795162042bdeafbe8187a62378316817b1caa"
genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash")

# --- UTILITY FUNCTIONS ---

def fetch_trending_topics():
    try:
        url = f"https://newsdata.io/api/1/news?country=in&language=en&apikey={NEWSDATA_API_KEY}"
        response = requests.get(url)
        articles = response.json().get("results", [])
        return [article['title'] for article in articles[:10]]
    except Exception as e:
        return ["Trending topics not available. Try later."]

def generate_tenglish_meme(topic):
    prompt = f"""
You're a witty meme writer for a Telugu meme page.

🎯 Goal:
Generate a **funny, clean, well-structured meme in Tenglish** (Telugu + English). The meme should feel natural and scroll-worthy on Instagram or Twitter.

📝 Structure:
- Format: **Two lines only**
  - **Line 1**: Setup (the situation or dialogue)
  - **Line 2**: Punchline (a funny or relatable twist)
- Keep it **short, grammatically clean**, and **easy to read**
- Use **Tenglish**, not full Hinglish or local slang (no "ra", "le", "abba", etc.)
- Avoid over-explaining or overcomplicating
- Don’t force rhymes or use broken Telugu-English combinations
- Make sure the meme is **understandable instantly**

📌 Examples:

1.
Line 1: Professor: “Identify this bone.”
Line 2: Me: “Sir... naku books lo chusina bone okkate gurthu undi.”

2.
Line 1: Friend: “Exam easy undha?”
Line 2: Me: “Question chusinappude memory loss start ayyindi.”

3.
Line 1: Amma: “Morning walk ki vellava?”
Line 2: Me: “Dream lo 3 rounds veyyadam jarigindi!”

Now write a meme for the topic: **{topic}**
Only output the two meme lines. Nothing else.
"""
    try:
        response = gemini.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating meme: {e}"


def generate_fun_reply():
    prompt = """
Generate a funny, one-liner witty reply in Hyderabadi Tenglish style.
Make it feel like something you'd hear at a pan shop or chai adda.
Keep it under 2 lines. No vulgarity.

Examples:
- “Life ante Biriyani... kaani mana plate lo empty leaf undi bro!”
- “Brain ke signals icchina... heart antenna block chesindi.”
- “Love ante cinema la untadi... real lo popcorn kuda share cheyyaru.”

Only output the line. Nothing else.
"""
    try:
        response = gemini.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "No joke this time boss... Gemini silent ayipoyindi 😂"

# --- STREAMLIT APP ---

st.set_page_config(page_title="Tenglish Meme Bot 😂", page_icon="😂")
st.title("Tenglish Meme Bot 😂")
st.caption("Unwind with spicy memes, trending madness & Hyderabadi one-liners.")
st.markdown("---")

menu = st.sidebar.radio("👀 What do you want to do?", ["Meme Generation", "Trending Topics", "Fun Chat & Replies", "Exit"])

# --- MEME GENERATION FLOW ---
if menu == "Meme Generation":
    st.subheader("🎭 Generate a Tenglish Meme")

    if st.toggle("📌 I want to give my own topic"):
        user_topic = st.text_input("Enter your meme topic:")
        if user_topic and st.button("Generate Meme"):
            meme = generate_tenglish_meme(user_topic)
            st.success("Here’s your meme:")
            st.markdown(f"💬 {meme}")
    else:
        if st.button("Generate Random Meme"):
            random_topics = [
                "Traffic in Hyderabad", "Exam Results", "Sambar vs Pappu",
                "Raining in Ameerpet", "Biryani Shortage", "No internet",
                "Boss Call on Weekend", "College Attendance", "Crush Reply Delay",
                "Salary Before Month End"
            ]
            meme = generate_tenglish_meme(random.choice(random_topics))
            st.success("Here’s your meme:")
            st.markdown(f"💬 {meme}")

    if st.toggle("✏️ Edit the Meme"):
        edited = st.text_input("Edit your meme:")
        if edited:
            st.markdown(f"✅ Final Meme: **{edited}**")
    else:
        st.markdown("✅ Final Meme confirmed.")

    if st.button("🔁 Want Another Meme?"):
        st.experimental_rerun()

# --- TRENDING TOPICS FLOW ---
elif menu == "Trending Topics":
    st.subheader("🔥 Real-Time Trending Topics")
    topics = fetch_trending_topics()

    if "Trending topics not available" in topics[0]:
        st.error(topics[0])
    else:
        selected = st.selectbox("Pick a trending topic for your meme:", topics)
        if st.button("Generate Meme on Trending Topic"):
            meme = generate_tenglish_meme(selected)
            st.success("Here’s your meme:")
            st.markdown(f"💬 {meme}")

# --- FUN CHAT & REPLIES FLOW ---
elif menu == "Fun Chat & Replies":
    st.subheader("Fun Mode")
    if st.button("Tell me a funny line!"):
        joke = generate_fun_reply()
        st.markdown(f"🎉 {joke}")

# --- EXIT FLOW ---
elif menu == "Exit":
    st.markdown("👋 Chill le ra bhai... Come back anytime!")


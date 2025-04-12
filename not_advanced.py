import streamlit as st
import requests
import google.generativeai as genai
import random
from PIL import Image, ImageDraw, ImageFont
import pyttsx3
import base64
from io import BytesIO

# Config
GEMINI_API_KEY = "AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM"
NEWSDATA_API_KEY = "pub_795162042bdeafbe8187a62378316817b1caa"
genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash")

# Text-to-speech engine
tts_engine = pyttsx3.init()

# --- UTILITY FUNCTIONS ---

def fetch_trending_topics():
    try:
        url = f"https://newsdata.io/api/1/news?country=in&language=en&apikey={NEWSDATA_API_KEY}"
        response = requests.get(url)
        articles = response.json().get("results", [])
        return [article['title'] for article in articles[:10]]
    except Exception:
        return ["Trending topics not available. Try later."]

def generate_tenglish_meme(topic: str, allow_double_meaning: bool = False) -> str:
    double_meaning_note = (
        "✅ Double meaning allowed: You may include light, witty double-meaning humor like subtle adult Telugu movie jokes. Keep it **classy, clever, and NOT vulgar**."
        if allow_double_meaning else
        "🚫 No double-meaning jokes. Keep it clean, witty, and family-friendly."
    )

    prompt = f'''
You are a professional meme writer for a Telugu + English (Tenglish) meme page.

🎯 Task:
Write a **2-line** meme in **Tenglish** — the meme should be **funny**, **natural**, and **clearly structured**.

🛠 Format Rules:
- STRICTLY output **only 2 lines**.
- Line 1: Setup or situation.
- Line 2: Punchline — a twist, funny response, or inner thought.
- Keep it short, grammatically clean, and scroll-friendly.
- **Avoid** Hyderabadi-specific slang (like "abba", "ra", "le", "baigan", etc).
- Use natural Telugu-English like: "nenu", "vachindi", "chusina", "undhi", etc.
- Make sure the meme **makes sense even if read in 3 seconds**.
- Avoid rhyming or forced humor.
- Don't add explanations, emojis, or extra text — just the meme.

📘 Examples:

Line 1: Professor: “Identify this bone.”
Line 2: Me: “Sir... books lo chusina bone okkate gurthu undi.”

Line 1: Crush: "I'm dating someone else."
Line 2: Nenu: "Same pinch... naa life kooda heartbreak tho dating chesthundi."

Line 1: Girl: "You like deep things?"
Line 2: Me: "Regret lo depth undhi... nenu daily swim chestha."

📎 Topic: {topic}
{double_meaning_note}

⚠️ Final Output:
Just print the 2-line meme exactly like this:

Line 1: <your setup>
Line 2: <your punchline>
'''
    return prompt


    try:
        response = gemini.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating meme: {e}"

def generate_fun_reply():
    prompt = """
You're a fun-loving Hyderabadi joker. Give me a funny one-liner, like a savage reply or clever roast. Make it short and original in Hinglish or Tenglish.

Examples:
- "Life lo clarity kante memes ekkuva undi."
- "Salary endhuku? Just for recharging emotions monthly."

Give just one funny line.
"""
    try:
        response = gemini.generate_content(prompt)
        return response.text.strip()
    except:
        return "No joke today boss... AI too is laughing!"

def meme_to_image(meme_text):
    lines = meme_text.split("\n")
    image = Image.new("RGB", (700, 250), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()

    y = 50
    for line in lines:
        draw.text((50, y), line.strip(), font=font, fill=(0, 0, 0))
        y += 40

    return image

def convert_image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    return base64.b64encode(img_bytes).decode()

def speak_meme(meme_text):
    tts_engine.say(meme_text)
    tts_engine.runAndWait()

# --- STREAMLIT UI ---

st.set_page_config(page_title="😂 Tenglish Meme Bot", page_icon="😂", layout="centered")
st.title("😂 Tenglish Meme Bot")
st.caption("Unwind with memes, trending madness & Hyderabadi jokes.")
st.markdown("---")

menu = st.sidebar.radio("👀 What do you want to do?", ["Meme Generation", "Trending Topics", "Fun Chat & Replies", "Exit"])
dark_mode = st.sidebar.checkbox("🌙 Dark Mode")

if dark_mode:
    st.markdown(
        """
        <style>
        body {
            background-color: #0E1117;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True
    )

# --- MEME GENERATION ---
if menu == "Meme Generation":
    st.subheader("🎭 Generate a Tenglish Meme")

    if st.toggle("📌 I want to give my own topic"):
        user_topic = st.text_input("Enter your meme topic:")
        if user_topic and st.button("Generate Meme"):
            meme = generate_tenglish_meme(user_topic)
            st.success("Here’s your meme:")
            st.markdown(f"💬 **{meme}**")
    else:
        if st.button("Generate Random Meme"):
            random_topics = ["Traffic in Hyderabad", "Exam Results", "Sambar vs Pappu", "Raining in Ameerpet", "Biryani Shortage", "No internet", "Boss Call on Weekend"]
            meme = generate_tenglish_meme(random.choice(random_topics))
            st.success("Here’s your meme:")
            st.markdown(f"💬 **{meme}**")

    if 'meme' in locals():
        if st.button("🖼 Convert to Meme Image"):
            meme_img = meme_to_image(meme)
            st.image(meme_img, caption="Download or Share!")
            base64_img = convert_image_to_base64(meme_img)
            href = f'<a href="data:file/png;base64,{base64_img}" download="meme.png">📥 Download Meme</a>'
            st.markdown(href, unsafe_allow_html=True)

        if st.button("🔊 Voice it Out"):
            speak_meme(meme)

        if st.button("📋 Copy to Clipboard"):
            st.code(meme, language='')

    # Edit option
    if st.toggle("✏️ Edit the Meme"):
        edited = st.text_area("Edit your meme:", value=meme if 'meme' in locals() else "")
        if edited:
            st.markdown(f"✅ Final Meme: **{edited}**")
    else:
        st.markdown("✅ Final Meme confirmed.")

    if st.button("🔁 Want Another Meme?"):
        st.experimental_rerun()

# --- TRENDING TOPICS ---
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
            st.markdown(f"💬 **{meme}**")

# --- FUN CHAT & REPLIES ---
elif menu == "Fun Chat & Replies":
    st.subheader("🤣 Hyderabadi Fun Mode")
    if st.button("Tell me a funny line!"):
        joke = generate_fun_reply()
        st.markdown(f"🎉 **{joke}**")

# --- EXIT ---
elif menu == "Exit":
    st.markdown("👋 Chill le ra bhai... Come back anytime!")

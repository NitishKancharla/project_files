import streamlit as st
import speech_recognition as sr
import pyttsx3
import fitz
import tempfile
import threading
from google.generativeai import GenerativeModel, configure

# --------------- CONFIG ------------------
configure(api_key="AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM")
model = GenerativeModel("gemini-1.5-flash")
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# --------------- SPEAK ------------------
def speak(text):
    def run():
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=run).start()

# --------------- LISTEN ------------------
def record_audio():
    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening... please start speaking.")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=30, phrase_time_limit=300)
        return audio
    except sr.WaitTimeoutError:
        return None
    except Exception as e:
        return f"Error while recording: {str(e)}"

def transcribe_audio(audio):
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand your answer."
    except Exception as e:
        return f"Transcription error: {str(e)}"

# --------------- PARSE RESUME ------------------
def extract_text(file):
    if file.name.endswith(".pdf"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(file.read())
            tmp_pdf_path = tmp_pdf.name
        doc = fitz.open(tmp_pdf_path)
        return "\n".join(page.get_text() for page in doc)
    elif file.name.endswith(".txt"):
        return file.read().decode('utf-8', errors='ignore')
    else:
        return "Unsupported file type."

# --------------- AI QUESTIONS ------------------
def get_question(resume_text, last_answer=None):
    prompt = f"""You are a helpful technical interviewer. Based on this resume:
{resume_text}

Ask a short, technical, specific question. {f"This should follow up on this answer: {last_answer}" if last_answer else ""} Keep it under 40 words.
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def get_feedback(resume_text, conversation):
    dialogue = "\n".join([f"Q: {qa['q']}\nA: {qa['a']}" for qa in conversation])
    prompt = f"""Give helpful feedback for this interview based on the resume and Q&A.

Resume:
{resume_text}

Interview Conversation:
{dialogue}
"""
    return model.generate_content(prompt).text.strip()

# --------------- STREAMLIT APP ------------------
st.set_page_config("AI Interviewer", layout="centered")
st.title("🤖 Smart Interview Simulator")

uploaded_file = st.file_uploader("📄 Upload Resume (PDF or TXT)", type=["pdf", "txt"])

if uploaded_file:
    resume = extract_text(uploaded_file)

    if "step" not in st.session_state:
        st.session_state.step = 0
        st.session_state.qa = []
        st.session_state.curr_q = ""
        st.session_state.recording = False
        st.session_state.audio = None
        st.session_state.answer = ""

    if st.session_state.step < 3:

        if st.session_state.curr_q == "":
            with st.spinner("Generating next question..."):
                last_ans = st.session_state.qa[-1]["a"] if st.session_state.qa else None
                st.session_state.curr_q = get_question(resume, last_ans)
                st.session_state.answer = ""
                st.session_state.audio = None
                speak(st.session_state.curr_q)

        st.subheader(f"❓ Question {st.session_state.step + 1}")
        st.markdown(f"**{st.session_state.curr_q}**")

        if not st.session_state.recording:
            if st.button("🎙️ Start Recording"):
                st.session_state.audio = record_audio()
                st.session_state.recording = True
                st.rerun()
        else:
            if st.button("✅ Done"):
                if st.session_state.audio:
                    st.session_state.answer = transcribe_audio(st.session_state.audio)
                    st.session_state.qa.append({"q": st.session_state.curr_q, "a": st.session_state.answer})
                    st.session_state.curr_q = ""
                    st.session_state.recording = False
                    st.session_state.step += 1
                    st.rerun()
                else:
                    st.warning("⚠️ No audio was recorded. Please try again.")
        
        if st.session_state.answer:
            st.write("🗣️ Your Answer:")
            st.write(st.session_state.answer)

    else:
        st.subheader("🎓 Interview Summary & Feedback")
        feedback = get_feedback(resume, st.session_state.qa)
        st.success("✅ Interview Completed")
        st.write(feedback)

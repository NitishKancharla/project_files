import streamlit as st
import pdfplumber
import docx
import tempfile
import time
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from google.generativeai import GenerativeModel, configure
import threading
import logging
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os

# --- Setup Gemini ---
configure(api_key="AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM")
gemini_model = GenerativeModel("gemini-1.5-flash")
logging.basicConfig(filename='ai_interview.log', level=logging.INFO)

# Load Whisper model
model = WhisperModel("small", compute_type="int8")

# Global flag for stopping recording
stop_listening_flag = False

# ========== HELPER FUNCTIONS ==========

def extract_resume_text(file_path):
    text = ""
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            if not text.strip():  # fallback to OCR if text is empty
                images = convert_from_path(file_path)
                ocr_text = ""
                for image in images:
                    ocr_text += pytesseract.image_to_string(image) + "\n"
                return ocr_text
            return text
        elif file_path.endswith(".docx"):
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        else:
            raise ValueError("Only PDF or DOCX files are supported.")
    except Exception as e:
        logging.error(f"Resume extraction failed: {e}")
        return "Failed to extract resume content."

def record_audio(duration=120, sample_rate=16000):
    st.info("🎤 Recording started... Speak now.")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    
    def stop_button_thread():
        global stop_listening_flag
        if st.button("✅ Done (Finish Answer)"):
            stop_listening_flag = True

    threading.Thread(target=stop_button_thread).start()

    start_time = time.time()
    while time.time() - start_time < duration:
        if stop_listening_flag:
            sd.stop()
            break
        time.sleep(0.1)

    sd.stop()
    return audio.squeeze(), sample_rate

def transcribe_audio(audio_data, sample_rate):
    segments, _ = model.transcribe(audio_data, language="en", beam_size=5)
    result = " ".join([seg.text for seg in segments])
    return result.strip() or "Sorry, I couldn't understand your answer."

def smart_listen():
    global stop_listening_flag
    stop_listening_flag = False
    audio_data, sample_rate = record_audio()
    return transcribe_audio(audio_data, sample_rate)

def generate_question(resume_text, previous_answer=None):
    prompt = (
        f"Generate an interview question based on this resume:\n{resume_text}"
        if not previous_answer else
        f"Ask a follow-up technical question based on this resume and previous answer.\nResume:\n{resume_text}\nAnswer:\n{previous_answer}"
    )
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(f"Gemini API error: {e}")
        return "Sorry, I couldn't generate the next question."

def generate_feedback(resume_text, responses):
    compiled = "\n".join([f"Q: {r['question']}\nA: {r['answer']}" for r in responses])
    prompt = f"Provide constructive feedback for this interview. Resume:\n{resume_text}\nInterview log:\n{compiled}"
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(f"Feedback generation error: {e}")
        return "Feedback generation failed."

# ========== STREAMLIT UI ==========

st.set_page_config(page_title="AI Voice Interviewer (OCR Enhanced)", layout="centered")
st.title("🎙️ AI Interviewer (With OCR for Resumes)")
st.markdown("Upload your resume (PDF or DOCX). AI will read it, ask questions, and record your voice answers!")

uploaded_file = st.file_uploader("Upload your Resume (.pdf or .docx)", type=["pdf", "docx"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp:
        tmp.write(uploaded_file.read())
        file_path = tmp.name

    resume_text = extract_resume_text(file_path)
    if resume_text.strip():
        st.success("✅ Resume parsed successfully!")
        st.text_area("📄 Extracted Resume Text", resume_text, height=200)

        if st.button("Start Interview"):
            responses = []

            for i in range(3):
                with st.spinner(f"Generating Question {i+1}..."):
                    question = generate_question(resume_text, previous_answer=responses[-1]['answer'] if responses else None)

                st.markdown(f"**Question {i+1}:** {question}")
                st.write("Please answer after the beep. You have up to 2 minutes to respond. Click ✅ when done.")
                time.sleep(1)

                answer = smart_listen()
                st.markdown(f"**Your Answer:** {answer}")
                responses.append({"question": question, "answer": answer})
                time.sleep(2)

            st.subheader("📋 Interview Feedback")
            feedback = generate_feedback(resume_text, responses)
            st.success("✅ Interview completed!")
            st.markdown(feedback)
    else:
        st.error("❌ Could not extract text from resume. Please try a different file.")

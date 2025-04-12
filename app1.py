import streamlit as st
import speech_recognition as sr
import pdfplumber
import docx
import tempfile
from google.generativeai import GenerativeModel, configure
import time
import threading
import logging

# --- Setup Gemini ---
configure(api_key="AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM")  # Replace with your actual key
gemini_model = GenerativeModel("gemini-1.5-flash")
logging.basicConfig(filename='ai_interview.log', level=logging.INFO)

# --- Global flag for ending early ---
stop_listening_flag = False


# ========== HELPER FUNCTIONS ==========

def extract_resume_text(file_path):
    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        raise ValueError("Only PDF or DOCX allowed")


def smart_listen(timeout=30, max_duration=120, silence_threshold=20):
    global stop_listening_flag
    stop_listening_flag = False

    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    st.info("🎤 Waiting for your answer (you have 30 seconds to start)...")

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        start_time = time.time()
        audio_data = sr.AudioData(b"", source.SAMPLE_RATE, source.SAMPLE_WIDTH)
        last_speech_time = None
        recording = False

        # Start a thread for stop button
        def stop_button_thread():
            global stop_listening_flag
            if st.button("✅ Done (Finish Answer)"):
                stop_listening_flag = True

        threading.Thread(target=stop_button_thread).start()

        while True:
            if stop_listening_flag:
                break

            try:
                chunk = recognizer.listen(source, timeout=1, phrase_time_limit=5)
                if not recording:
                    st.info("🗣️ Detected voice! Recording answer now (up to 2 minutes)...")
                    recording = True
                audio_data = sr.AudioData(audio_data.frame_data + chunk.frame_data,
                                          source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                last_speech_time = time.time()

                if time.time() - start_time > max_duration:
                    break
            except sr.WaitTimeoutError:
                if not recording:
                    if time.time() - start_time > timeout:
                        return "No answer provided within 30 seconds."
                else:
                    if last_speech_time and (time.time() - last_speech_time > silence_threshold):
                        break
                    elif time.time() - start_time > max_duration:
                        break
            except Exception as e:
                return f"Speech error: {e}"

    try:
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand your answer."
    except Exception as e:
        return f"Recognition error: {e}"


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

st.set_page_config(page_title="AI Voice Interviewer", layout="centered")
st.title("🎙️ AI Interviewer (Smart Voice Mode + Done Button)")
st.markdown("Upload your resume, and the AI will interview you. Speak your answers!")

uploaded_file = st.file_uploader("Upload your Resume (.pdf or .docx)", type=["pdf", "docx"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp:
        tmp.write(uploaded_file.read())
        file_path = tmp.name

    resume_text = extract_resume_text(file_path)
    st.success("✅ Resume parsed successfully!")

    if st.button("Start Interview"):
        responses = []

        for i in range(3):  # Increase to 5 if needed
            with st.spinner(f"Generating Question {i+1}..."):
                question = generate_question(resume_text, previous_answer=responses[-1]['answer'] if responses else None)

            st.markdown(f"**Question {i+1}:** {question}")
            st.write("Please answer after the beep. You have 30 seconds to start, up to 2 minutes to respond, and pauses longer than 20s will end the answer.")
            time.sleep(1)  # mimic beep

            answer = smart_listen()
            st.markdown(f"**Your Answer:** {answer}")
            responses.append({"question": question, "answer": answer})
            time.sleep(2)

        st.subheader("📋 Interview Feedback")
        feedback = generate_feedback(resume_text, responses)
        st.success("✅ Interview completed!")
        st.markdown(feedback)
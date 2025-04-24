import pdfplumber
from google.generativeai import GenerativeModel, configure
from faster_whisper import WhisperModel
import logging
import soundfile as sf
import numpy as np
import pickle
import os

# Setup Gemini API
configure(api_key="AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM")
gemini_model = GenerativeModel("gemini-1.5-flash")

# Setup logging
logging.basicConfig(filename='persimmon.log', level=logging.INFO)

# Initialize Whisper model
whisper_model = WhisperModel("small", compute_type="int8")

def extract_resume_text(file_path):
    """Extract text from a PDF resume."""
    try:
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        logging.info(f"Extracted resume text length: {len(text)}")
        return text if text else "Error extracting text from PDF"
    except Exception as e:
        logging.error(f"Resume extraction error: {e}")
        return "Error extracting text from PDF"

def compute_match_score(resume_text, jd_text):
    """Compute match score between resume and JD using Gemini."""
    prompt = f"""
    Analyze the following resume and job description. Determine the match score as a percentage based on skills, experience, and qualifications.
    Resume: {resume_text}
    Job Description: {jd_text}
    Return only the percentage score (e.g., 75).
    """
    try:
        response = gemini_model.generate_content(prompt)
        score = float(response.text.strip())
        logging.info(f"Computed match score: {score}")
        return score
    except Exception as e:
        logging.error(f"Match score error: {e}")
        return 0

def generate_interview_question(resume_text, previous_answers=None):
    """Generate an interview question based on resume and previous answers."""
    prompt = (
        f"Generate a relevant interview question based on this resume:\n{resume_text}"
        if not previous_answers else
        f"Generate a follow-up interview question based on this resume and previous answers.\nResume:\n{resume_text}\nPrevious Answers:\n{'; '.join(previous_answers)}"
    )
    try:
        response = gemini_model.generate_content(prompt)
        question = response.text.strip()
        logging.info(f"Generated question: {question[:50]}...")
        return question
    except Exception as e:
        logging.error(f"Question generation error: {e}")
        return "Sorry, I couldn't generate the next question."

def transcribe_audio(audio_path):
    """Transcribe audio file using Faster Whisper."""
    try:
        segments, _ = whisper_model.transcribe(audio_path, language="en", beam_size=5)
        result = " ".join([seg.text for seg in segments])
        logging.info(f"Transcribed answer length: {len(result)}")
        return result.strip() or "Sorry, I couldn't understand your answer."
    except Exception as e:
        logging.error(f"Transcription error: {e}")
        return "Sorry, I couldn't understand your answer."

def save_audio(filename, audio_data, sample_rate=16000):
    """Save audio data to a WAV file."""
    try:
        if audio_data.ndim > 1:
            audio_data = audio_data.flatten()
        sf.write(filename, audio_data, sample_rate)
        logging.info(f"Saved audio to {filename}")
    except Exception as e:
        logging.error(f"Audio save error: {e}")
        raise

def generate_feedback(questions, answers):
    """Generate feedback based on interview responses."""
    compiled = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)])
    prompt = f"""
    Provide constructive feedback for this interview based on the questions and answers.
    Interview Log:\n{compiled}
    Highlight strengths and areas for improvement.
    """
    try:
        response = gemini_model.generate_content(prompt)
        feedback = response.text.strip()
        logging.info(f"Generated feedback length: {len(feedback)}")
        return feedback
    except Exception as e:
        logging.error(f"Feedback generation error: {e}")
        return "Feedback generation failed."

def store_state(session_id, state_data):
    """Store state to disk."""
    try:
        state_file = f"state_{session_id}.pkl"
        with open(state_file, 'wb') as f:
            pickle.dump(state_data, f)
        logging.info(f"Stored state for session_id: {session_id}")
    except Exception as e:
        logging.error(f"State storage error: {e}")
        raise

def retrieve_state(session_id):
    """Retrieve state from disk."""
    try:
        state_file = f"state_{session_id}.pkl"
        if os.path.exists(state_file):
            with open(state_file, 'rb') as f:
                state_data = pickle.load(f)
            logging.info(f"Retrieved state for session_id: {session_id}, resume_text_length: {len(state_data.get('resume_text', ''))}")
            return state_data
        logging.warning(f"No state file found for session_id: {session_id}")
        return {}
    except Exception as e:
        logging.error(f"State retrieval error: {e}")
        return {}
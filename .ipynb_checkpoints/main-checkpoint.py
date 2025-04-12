import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
from google.generativeai import GenerativeModel, configure
import os

# (Optional) Set this only on Windows if poppler isn't in PATH
# os.environ["PATH"] += os.pathsep + r"C:\path\to\poppler\bin"

# Gemini API setup
GEMINI_API_KEY = "AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM"
configure(api_key=GEMINI_API_KEY)
MODEL = "gemini-1.5-flash"
gemini_model = GenerativeModel(MODEL)

def extract_text_from_pdf(uploaded_file):
    text = ""

    # Read the file once and reuse
    file_bytes = uploaded_file.read()

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print("pdfplumber error:", e)

    # Fallback to OCR if no text found
    if not text.strip():
        st.warning("No selectable text found. Using OCR...")
        try:
            images = convert_from_bytes(file_bytes)
            for img in images:
                text += pytesseract.image_to_string(img) + "\n"
        except Exception as e:
            st.error(f"OCR failed: {e}")
            return "Error: Unable to extract text from PDF."

    return text.strip() if text.strip() else "Error: No text found in the PDF."


def summarize_resume(text):
    prompt = f"Summarize this resume:\n\n{text}"
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

def get_initial_question(resume_summary):
    prompt = f"Generate an opening interview question based on this resume summary:\n\n{resume_summary}"
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

def validate_answer(question, answer):
    prompt = f"""
    Evaluate this answer to the question. Respond only with "Valid" or "Incorrect".

    Question: {question}
    Answer: {answer}
    """
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

def check_grammar(answer):
    prompt = f"Correct any grammar issues in this answer:\n\n{answer}"
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

def get_followup_question(convo_history):
    prompt = f"Generate a follow-up interview question based on this conversation:\n\n{convo_history}"
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

def generate_performance_review(convo_history):
    prompt = f"""
    Review the candidate's answers in this conversation. Provide:
    - Strengths
    - Weaknesses
    - Overall performance

    Conversation:
    {convo_history}
    """
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

# Streamlit UI
st.title("🎯 Resume AI Interviewer")
uploaded_file = st.sidebar.file_uploader("Upload Resume (PDF)", type="pdf")

if uploaded_file:
    resume_text = extract_text_from_pdf(uploaded_file)
    resume_summary = summarize_resume(resume_text)

    st.subheader("📄 Resume Summary")
    st.write(resume_summary)

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "questions_asked" not in st.session_state:
        st.session_state.questions_asked = 0
    if "current_question" not in st.session_state:
        st.session_state.current_question = get_initial_question(resume_summary)
        st.session_state.conversation_history.append(f"🤖 AI: {st.session_state.current_question}")
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""

    st.subheader("💬 Interactive Interview")

    for chat in st.session_state.conversation_history:
        st.write(chat)

    st.session_state.user_input = st.text_input("Your Answer:", value=st.session_state.user_input)

    if st.button("Submit"):
        user_input = st.session_state.user_input.strip()

        if user_input:
            st.session_state.conversation_history.append(f"**You:** {user_input}")
            st.session_state.questions_asked += 1

            validation_result = validate_answer(st.session_state.current_question, user_input)

            if validation_result == "Valid":
                st.write("✅ Valid answer.")
                grammar_feedback = check_grammar(user_input)
                st.write("📝 Grammar Feedback:")
                st.write(grammar_feedback)

                if st.session_state.questions_asked < 5:
                    next_q = get_followup_question("\n".join(st.session_state.conversation_history))
                    st.session_state.current_question = next_q
                    st.session_state.conversation_history.append(f"🤖 AI: {next_q}")
                    st.session_state.user_input = ""
                else:
                    review = generate_performance_review("\n".join(st.session_state.conversation_history))
                    st.session_state.conversation_history.append(f"📊 Final Review:\n{review}")
                    st.session_state.current_question = "Interview Complete"

            else:
                st.write("❌ Incorrect answer. Try again or skip.")
                if st.session_state.questions_asked < 5:
                    next_q = get_followup_question("\n".join(st.session_state.conversation_history))
                    st.session_state.current_question = next_q
                    st.session_state.conversation_history.append(f"🤖 AI: {next_q}")
                else:
                    review = generate_performance_review("\n".join(st.session_state.conversation_history))
                    st.session_state.conversation_history.append(f"📊 Final Review:\n{review}")
                    st.session_state.current_question = "Interview Complete"

            st.rerun()

import streamlit as st
import pdfplumber
from google.generativeai import GenerativeModel, configure

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM"  # Replace with your Gemini API key
configure(api_key=GEMINI_API_KEY)
MODEL = "gemini-1.5-flash"
gemini_model = GenerativeModel(MODEL)

# Extract text from PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text if text else "Error extracting text from PDF"

# Summarize resume content
def summarize_resume(text):
    prompt = f"Summarize the following resume in a structured format:\n\n{text}"
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

# Generate initial question
def get_initial_question(resume_summary):
    prompt = f"Generate a relevant opening interview question based on this resume summary:\n\n{resume_summary}"
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

# Validate answer correctness
def validate_answer(question, answer):
    prompt = f"""
    You are an AI interviewer evaluating if the candidate's response is relevant to the question.

    Instructions:
    - If the answer correctly addresses the question, return "Valid".
    - If the answer is incorrect, irrelevant, or unrelated, return "Incorrect".

    Question: {question}
    Answer: {answer}

    Respond only with "Valid" or "Incorrect".
    """
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

# Check grammar correctness
def check_grammar(answer):
    prompt = f"Analyze this answer for grammar mistakes and suggest improvements:\n\n{answer}"
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

# Generate follow-up question dynamically
def get_followup_question(conversation_history):
    prompt = f"""
    Based on this conversation history, generate the next logical follow-up question:

    {conversation_history}

    Ensure the question is relevant to previous responses.
    """
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

# Generate final performance review after 5 questions
def generate_performance_review(conversation_history):
    prompt = f"""
    You are an AI interviewer analyzing the candidate's performance.

    - Provide an overall assessment of their answers.
    - Highlight their strengths.
    - Mention areas for improvement.

    Here is the full conversation:

    {conversation_history}

    Generate a structured performance review.
    """
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

# Streamlit UI
st.title(" AI Resume Chatbot")
st.sidebar.header("Upload Resume")
uploaded_file = st.sidebar.file_uploader("Upload Resume (PDF)", type="pdf")

if uploaded_file:
    resume_text = extract_text_from_pdf(uploaded_file)
    resume_summary = summarize_resume(resume_text)

    st.subheader(" Resume Summary")
    st.write(resume_summary)

    # Initialize session state
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "questions_asked" not in st.session_state:
        st.session_state.questions_asked = 0
    if "current_question" not in st.session_state:
        st.session_state.current_question = get_initial_question(resume_summary)
        st.session_state.conversation_history.append(f" AI: {st.session_state.current_question}")
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""  # Store user input temporarily

    st.subheader(" AI Interactive Interview")

    # Display chat history
    for chat in st.session_state.conversation_history:
        st.write(chat)

    # User input for answering questions
    st.session_state.user_input = st.text_input("Your Answer:", value=st.session_state.user_input)

    if st.button("Submit"):
        user_input = st.session_state.user_input.strip()  # Prevent empty spaces

        if user_input:
            st.session_state.conversation_history.append(f"**You:** {user_input}")
            st.session_state.questions_asked += 1

            # Validate the answer
            validation_result = validate_answer(st.session_state.current_question, user_input)

            if validation_result == "Valid":
                st.write(" Your answer is relevant!")

                # Check grammar
                grammar_feedback = check_grammar(user_input)

                if "No issues" in grammar_feedback:
                    st.write(" **Feedback: Good Answer! No grammar mistakes.**")
                else:
                    st.write(f" **Feedback: Needs Improvement (Grammar Issues).**\n Grammar Feedback: {grammar_feedback}")

                # Ask next question if <5 questions asked
                if st.session_state.questions_asked < 5:
                    next_question = get_followup_question("\n".join(st.session_state.conversation_history))
                    st.session_state.current_question = next_question
                    st.session_state.conversation_history.append(f" AI: {next_question}")
                    st.session_state.user_input = ""  # Reset input field
                else:
                    # Generate final performance review after 5 questions
                    performance_review = generate_performance_review("\n".join(st.session_state.conversation_history))
                    st.session_state.conversation_history.append(f" **Final Performance Review:**\n\n{performance_review}")
                    st.session_state.current_question = "Interview Completed "

            else:  # If answer is incorrect
                st.write(" **Feedback: Incorrect Answer. Try again.**")
                st.session_state.user_input = ""  # Reset input field
                if st.session_state.questions_asked < 5:
                    next_question = get_followup_question("\n".join(st.session_state.conversation_history))
                    st.session_state.current_question = next_question
                    st.session_state.conversation_history.append(f" AI: {next_question}")
                    st.session_state.user_input = ""  # Reset input field
                else:
                    # Generate final performance review after 5 questions
                    performance_review = generate_performance_review("\n".join(st.session_state.conversation_history))
                    st.session_state.conversation_history.append(f" **Final Performance Review:**\n\n{performance_review}")
                    st.session_state.current_question = "Interview Completed "

            st.rerun()  # Refresh UI only after button click
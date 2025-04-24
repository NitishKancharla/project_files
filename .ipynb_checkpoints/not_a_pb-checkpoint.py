import streamlit as st
import fitz  # PyMuPDF for PDFs
import re
import json
from google.generativeai import GenerativeModel, configure
import io

# --- Configure Gemini ---
GEMINI_API_KEY = "AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM"
configure(api_key=GEMINI_API_KEY)
model = GenerativeModel("gemini-1.5-flash")

# --- Helper Functions ---
def extract_text_from_pdf(file_bytes):
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def parse_with_gemini(resume_text, jd_text):
    prompt = f"""
    You are a smart HR AI assistant. Analyze the following resume and job description to extract:

    1. Candidate location (city or region)
    2. Job location (city or region)
    3. Extract and rank the top 3 technical or domain-specific skills from the JD
    4. Identify if the candidate appears to be a fresher (less than 1 year experience) based on resume

    Resume:
    {resume_text}

    Job Description:
    {jd_text}

    Respond in this exact JSON format:
    {{
    "candidate_location": "City",
    "job_location": "City",
    "skills_from_jd": ["skill1", "skill2", "skill3"],
    "appears_fresher": true or false
    }}
    
    Make sure the JSON is properly formatted. For boolean values use lowercase true/false.
    """
    response = model.generate_content(prompt)
    match = re.search(r"\{.*\}", response.text, re.DOTALL)
    if match:
        # Use json.loads instead of eval to properly handle JavaScript-style booleans
        json_str = match.group()
        # Convert JavaScript-style true/false to Python True/False
        json_str = json_str.replace('true', 'True').replace('false', 'False')
        return eval(json_str)  # Now safe to eval with Python booleans
    return None

def get_dynamic_questions(parsed_data):
    questions = []

    # Location check
    if parsed_data["candidate_location"].lower() != parsed_data["job_location"].lower():
        questions.append(
            f"The job is located in **{parsed_data['job_location']}**, but you're based in **{parsed_data['candidate_location']}**. Are you willing to relocate to {parsed_data['job_location']}?"
        )

    # Fresher check first to determine follow-up questions
    questions.append("Are you a fresher (less than 1 year experience)? (Yes/No)")
    
    # Skills-based questions (for top 3 skills)
    for skill in parsed_data["skills_from_jd"]:
        questions.append(f"Rate your proficiency in {skill} on a scale of 1-10:")
        questions.append(f"How many years of experience do you have working with {skill}?")
    
    # These questions will be dynamically skipped or added based on fresher response
    # We'll handle this logic in the UI flow
    
    return questions

# --- Streamlit UI ---
st.title("🤖 AI Resume Prescreening Chatbot")
st.markdown("Upload your resume and the job description. I'll ask smart questions based on them!")

# Initialize session state variables
if 'step' not in st.session_state:
    st.session_state['step'] = 0
    st.session_state['chat_history'] = []
    st.session_state['answers'] = []
    st.session_state['questions'] = []
    st.session_state['parsed_data'] = None
    st.session_state['resume_content'] = None  # To store resume content
    st.session_state['jd_content'] = ""  # To store job description content
    st.session_state['initialized'] = False
    st.session_state['is_fresher'] = None
    st.session_state['dynamic_questions_added'] = False

# File uploader and text area for first-time input
col1, col2 = st.columns(2)
with col1:
    uploaded_resume = st.file_uploader("📄 Upload Resume (PDF only)", type=["pdf"])
with col2:
    job_description = st.text_area("📋 Paste Job Description", height=150)

# If resume is uploaded, save its content to session state
if uploaded_resume is not None and st.session_state['resume_content'] is None:
    # Read and store the file content
    file_bytes = uploaded_resume.getvalue()
    st.session_state['resume_content'] = file_bytes

# If job description is entered, save it to session state
if job_description and st.session_state['jd_content'] == "":
    st.session_state['jd_content'] = job_description

# Process the data when we have both resume and job description
if (st.session_state['resume_content'] is not None and 
    st.session_state['jd_content'] and 
    st.session_state['parsed_data'] is None):
    
    with st.spinner("🔍 Reading and analyzing resume and JD..."):
        try:
            resume_text = extract_text_from_pdf(st.session_state['resume_content'])
            parsed_data = parse_with_gemini(resume_text, st.session_state['jd_content'])

            if parsed_data:
                st.success("✅ Extracted key info!")
                st.session_state['parsed_data'] = parsed_data
                st.session_state['questions'] = get_dynamic_questions(parsed_data)
                st.session_state['initialized'] = True
            else:
                st.error("❌ Failed to extract data. Please ensure your files are valid.")
                # Reset the state to allow re-upload
                st.session_state['resume_content'] = None
                st.session_state['jd_content'] = ""
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            # Reset the state to allow re-upload
            st.session_state['resume_content'] = None
            st.session_state['jd_content'] = ""

# Once initialized, show the chat interface
if st.session_state['initialized']:
    # Create a divider
    st.markdown("---")
    st.subheader("💬 Chat Interface")
    
    # Display chat history (only previous exchanges)
    for i in range(len(st.session_state['chat_history'])):
        entry = st.session_state['chat_history'][i]
        st.markdown(f"**{entry['role']}**: {entry['message']}")

    # Check if we need to add or skip questions based on fresher status
    if st.session_state['step'] == 2 and st.session_state['is_fresher'] is not None and not st.session_state['dynamic_questions_added']:
        if st.session_state['is_fresher']:
            # Add only expected CTC question for freshers
            st.session_state['questions'].insert(2, "What is your expected CTC?")
        else:
            # Add all three questions for experienced candidates
            st.session_state['questions'].insert(2, "What is your current CTC?")
            st.session_state['questions'].insert(3, "What is your expected CTC?")
            st.session_state['questions'].insert(4, "What is your notice period (in days)?")
        
        st.session_state['dynamic_questions_added'] = True

    # Ask the next question based on the current step
    if st.session_state['step'] < len(st.session_state['questions']):
        current_question = st.session_state['questions'][st.session_state['step']]
        
        # Handle fresher question specially to capture response for dynamic questions
        if st.session_state['step'] == 1:  # Fresher question is at index 1
            # Display the section header for experience questions
            st.subheader("🧑‍💼 Experience and Compensation")
        
        # Only show skills header once before first skill question
        skill_question_index = 2 + (1 if st.session_state['is_fresher'] is True else 3 if st.session_state['is_fresher'] is False else 0)
        if st.session_state['step'] == skill_question_index and 'skills_header_shown' not in st.session_state:
            st.subheader("📌 Skill-Based Questions")
            st.session_state['skills_header_shown'] = True
        
        # Display the current question
        st.markdown(f"**AI**: {current_question}")
        
        # Get user input
        answer = st.text_input(f"Your answer to question {st.session_state['step'] + 1}", 
                              key=f"answer_{st.session_state['step']}")

        if st.button("Submit", key=f"submit_{st.session_state['step']}"):
            if answer:
                # Add the current question and answer to chat history
                if len(st.session_state['chat_history']) == 2 * st.session_state['step']:
                    st.session_state['chat_history'].append({"role": "AI", "message": current_question})
                st.session_state['chat_history'].append({"role": "User", "message": answer})
                st.session_state['answers'].append(answer)  # Store the user's answer
                
                # Check if this is the fresher question to determine next questions
                if st.session_state['step'] == 1:  # Fresher question is at index 1
                    st.session_state['is_fresher'] = answer.lower() in ["yes", "y", "true"]
                
                st.session_state['step'] += 1  # Move to the next question
                st.rerun()  # Use st.rerun() instead of experimental_rerun

    # Display all questions once all are answered
    if st.session_state['step'] >= len(st.session_state['questions']):
        st.markdown("**🎉 All questions answered! Here is a summary:**")
        
        # Create a summary of Q&A pairs
        for i in range(len(st.session_state['chat_history']) // 2):
            q_index = i * 2
            a_index = q_index + 1
            
            if a_index < len(st.session_state['chat_history']):
                question = st.session_state['chat_history'][q_index]['message']
                answer = st.session_state['chat_history'][a_index]['message']
                
                st.markdown(f"**Question {i+1}:** {question}")
                st.markdown(f"**Your Answer:** {answer}")
                st.markdown("---")
                
        # Add a reset button
        if st.button("Start New Assessment"):
            # Reset all state variables
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
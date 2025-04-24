import streamlit as st
import fitz  # PyMuPDF for PDFs
import re
import json
import sqlite3
from google.generativeai import GenerativeModel, configure
import io

# --- Configure Gemini ---
GEMINI_API_KEY = "AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM"
configure(api_key=GEMINI_API_KEY)
model = GenerativeModel("gemini-1.5-flash")

# --- Database Setup ---
conn = sqlite3.connect('match_scores.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS match_scores (
    candidate_name TEXT,
    candidate_location TEXT,
    job_location TEXT,
    match_score INTEGER,
    skills_match TEXT,
    experience_match TEXT,
    ctc_match TEXT
)
''')
conn.commit()

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
        json_str = match.group()
        json_str = json_str.replace('true', 'True').replace('false', 'False')
        return eval(json_str)
    return None

def get_dynamic_questions(parsed_data):
    questions = []

    if parsed_data["candidate_location"].lower() != parsed_data["job_location"].lower():
        questions.append(
            f"The job is located in **{parsed_data['job_location']}**, but you're based in **{parsed_data['candidate_location']}**. Are you willing to relocate to {parsed_data['job_location']}?"
        )

    questions.append("Are you a fresher (less than 1 year experience)? (Yes/No)")

    for skill in parsed_data["skills_from_jd"]:
        questions.append(f"Rate your proficiency in {skill} on a scale of 1-10:")
        questions.append(f"How many years of experience do you have working with {skill}?")
    
    return questions

def is_valid_ctc_answer(answer):
    pattern = r"^\s*\d+(\.\d+)?\s*(lpa|lakhs?|lacks?)\s*$"
    return bool(re.match(pattern, answer.strip().lower()))

def is_valid_fresher_answer(answer):
    return answer.lower() in ['yes', 'no']

def is_valid_notice_period(answer):
    pattern = r"^\s*(\d+)\s*(days?|month|months?)\s*$"
    return bool(re.match(pattern, answer.strip().lower()))

def is_valid_proficiency(answer):
    return answer.isdigit() and 1 <= int(answer) <= 10

def is_valid_experience_years(answer):
    return answer.isdigit() and int(answer) >= 0

def calculate_match_score(parsed_data, fresher_answer, proficiency_answers, experience_answers, ctc_answer):
    # Calculate match score components
    score = 0
    total_weight = 100

    # Location Match: 20%
    location_score = 20 if parsed_data["candidate_location"].lower() == parsed_data["job_location"].lower() else 0
    score += location_score

    # Skills Match: 40%
    skills_match = 0
    for i, skill in enumerate(parsed_data["skills_from_jd"]):
        if proficiency_answers[i] and int(proficiency_answers[i]) >= 6:
            skills_match += 13.33  # evenly divide the 40% across 3 skills
    score += skills_match

    # Experience Match: 30%
    experience_score = 0
    if fresher_answer.lower() in ['yes', 'y']:
        experience_score = 0 if parsed_data["appears_fresher"] else 30
    else:
        experience_score = int(experience_answers) / 10 * 30
    score += experience_score

    # CTC Match: 10%
    ctc_score = 10 if is_valid_ctc_answer(ctc_answer) else 0
    score += ctc_score

    # Return final score
    return score

def store_match_score(candidate_name, parsed_data, match_score, skills_match, experience_match, ctc_match):
    c.execute('''
    INSERT INTO match_scores (candidate_name, candidate_location, job_location, match_score, skills_match, experience_match, ctc_match)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (candidate_name, parsed_data["candidate_location"], parsed_data["job_location"], match_score, skills_match, experience_match, ctc_match))
    conn.commit()

# --- Streamlit UI ---
st.title("🤖 AI Resume Prescreening Chatbot")
st.markdown("Upload your resume and the job description. I'll ask smart questions based on them!")

if 'step' not in st.session_state:
    st.session_state['step'] = 0
    st.session_state['chat_history'] = []
    st.session_state['answers'] = []
    st.session_state['questions'] = []
    st.session_state['parsed_data'] = None
    st.session_state['resume_content'] = None
    st.session_state['jd_content'] = ""
    st.session_state['initialized'] = False
    st.session_state['is_fresher'] = None
    st.session_state['dynamic_questions_added'] = False
    st.session_state['proficiency_answers'] = []
    st.session_state['experience_answers'] = []

# File uploader and JD input
col1, col2 = st.columns(2)
with col1:
    uploaded_resume = st.file_uploader("📄 Upload Resume (PDF only)", type=["pdf"])
    if uploaded_resume:
        st.session_state['resume_content'] = uploaded_resume.getvalue()
with col2:
    jd_input = st.text_area("📋 Paste Job Description", height=150, value=st.session_state['jd_content'])
    st.session_state['jd_content'] = jd_input

# Processing
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
                st.session_state['resume_content'] = None
                st.session_state['jd_content'] = ""
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.session_state['resume_content'] = None
            st.session_state['jd_content'] = ""

# Chat interface
if st.session_state['initialized']:
    st.markdown("---")
    st.subheader("💬 Chat Interface")

    for entry in st.session_state['chat_history']:
        st.markdown(f"**{entry['role']}**: {entry['message']}")

    # Ask next question
    if st.session_state['step'] < len(st.session_state['questions']):
        current_question = st.session_state['questions'][st.session_state['step']]
        st.markdown(f"**AI**: {current_question}")
        answer = st.text_input(f"Your answer to question {st.session_state['step'] + 1}", 
                               key=f"answer_{st.session_state['step']}")

        if st.button("Submit", key=f"submit_{st.session_state['step']}"):
            if answer:
                st.session_state['chat_history'].append({"role": "User", "message": answer})
                st.session_state['answers'].append(answer)

                # Collect proficiency and experience answers
                if "rate your proficiency" in current_question.lower():
                    st.session_state['proficiency_answers'].append(answer)
                elif "years of experience" in current_question.lower():
                    st.session_state['experience_answers'].append(answer)
                elif "Are you a fresher" in current_question.lower():
                    st.session_state['is_fresher'] = answer

                # Move to next question
                st.session_state['step'] += 1

# --- Final Match Score ---
if st.session_state['step'] == len(st.session_state['questions']) and st.session_state['step'] > 0:
    match_score = calculate_match_score(st.session_state['parsed_data'], 
                                        st.session_state['is_fresher'], 
                                        st.session_state['proficiency_answers'], 
                                        st.session_state['experience_answers'],
                                        st.session_state['answers'][-1])

    st.markdown(f"### Your Match Score: {match_score:.2f}%")
    st.progress(match_score / 100)

    # Store results in database
    store_match_score("Candidate Name", st.session_state['parsed_data'], match_score, 
                      st.session_state['proficiency_answers'], 
                      st.session_state['experience_answers'], 
                      st.session_state['answers'][-1])
    
    st.session_state['step'] = 0  # Reset the steps after final match score

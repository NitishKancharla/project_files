import streamlit as st
import fitz  # PyMuPDF for PDFs
import re
import json
from google.generativeai import GenerativeModel, configure
import io

# --- Configure Gemini ---
GEMINI_API_KEY = "AIzaSyDStakIVWdsdtqFCwnHWHFMGbkGUgLJrQQ"
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

# --- Streamlit UI ---
st.title("🤖 AI Resume Prescreening Chatbot")
st.markdown("Upload your resume and the job description. I'll ask smart questions based on them!")

if 'step' not in st.session_state:
    st.session_state.update({
        'step': 0,
        'chat_history': [],
        'answers': [],
        'questions': [],
        'parsed_data': None,
        'resume_content': None,
        'jd_content': "",
        'initialized': False,
        'is_fresher': None,
        'dynamic_questions_added': False
    })

# Upload and input
col1, col2 = st.columns(2)
with col1:
    uploaded_resume = st.file_uploader("📄 Upload Resume (PDF only)", type=["pdf"])
    if uploaded_resume:
        st.session_state['resume_content'] = uploaded_resume.getvalue()
with col2:
    jd_input = st.text_area("📋 Paste Job Description", height=150, value=st.session_state['jd_content'])
    st.session_state['jd_content'] = jd_input

# Process resume and JD
if st.session_state['resume_content'] and st.session_state['jd_content'] and st.session_state['parsed_data'] is None:
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
                st.error("❌ Failed to extract data.")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# Chat interface
if st.session_state['initialized']:
    st.markdown("---")
    st.subheader("💬 Chat Interface")

    for entry in st.session_state['chat_history']:
        st.markdown(f"**{entry['role']}**: {entry['message']}")

    # Add compensation questions dynamically
    if st.session_state['step'] == 2 and st.session_state['is_fresher'] is not None and not st.session_state['dynamic_questions_added']:
        if st.session_state['is_fresher']:
            st.session_state['questions'].insert(2, "What is your expected CTC?")
        else:
            st.session_state['questions'].insert(2, "What is your current CTC?")
            st.session_state['questions'].insert(3, "What is your expected CTC?")
            st.session_state['questions'].insert(4, "What is your notice period (in days)?")
        st.session_state['dynamic_questions_added'] = True

    # Ask current question
    if st.session_state['step'] < len(st.session_state['questions']):
        q = st.session_state['questions'][st.session_state['step']]
        st.markdown(f"**AI:** {q}")
        input_response = None

        # Determine input type
        if "fresher" in q.lower() or "relocate" in q.lower():
            input_response = st.radio("Select one:", ["Yes", "No"], key=f"radio_{st.session_state['step']}")
        elif "rate your proficiency" in q.lower():
            input_response = st.slider("Select rating:", 1, 10, key=f"slider_{st.session_state['step']}")
        elif "years of experience" in q.lower():
            experience_options = [str(i) for i in range(10)]
            experience_options[-1] = "9+"
            input_response = st.selectbox("Select years:", experience_options, key=f"exp_{st.session_state['step']}")
        elif "ctc" in q.lower() or "notice period" in q.lower():
            input_response = st.text_input("Your answer:", key=f"text_{st.session_state['step']}")
        else:
            input_response = st.text_input("Your answer:", key=f"text_{st.session_state['step']}")

        if st.button("Submit", key=f"submit_{st.session_state['step']}"):
            answer = input_response

            # Validation
            if "ctc" in q.lower() and not re.match(r"^\s*\d+(\.\d+)?\s*(lpa|lakhs?|lacks?)\s*$", str(answer).strip().lower()):
                st.warning("❗ Please enter a valid CTC (e.g., 6 LPA, 6 lakhs).")
            elif "notice period" in q.lower() and not re.match(r"^\s*(\d+)\s*(days?|months?)\s*$", str(answer).strip().lower()):
                st.warning("❗ Please enter a valid notice period (e.g., 15 days, 1 month).")
            else:
                # Save chat
                if len(st.session_state['chat_history']) == 2 * st.session_state['step']:
                    st.session_state['chat_history'].append({"role": "AI", "message": q})
                st.session_state['chat_history'].append({"role": "User", "message": str(answer)})
                st.session_state['answers'].append(str(answer))

                if st.session_state['step'] == 1:
                    st.session_state['is_fresher'] = str(answer).lower() in ["yes", "y", "true"]

                st.session_state['step'] += 1
                st.rerun()

    if st.session_state['step'] >= len(st.session_state['questions']):
        st.markdown("**🎉 All questions answered! Here is a summary:**")
        for i in range(len(st.session_state['chat_history']) // 2):
            q_index = i * 2
            a_index = q_index + 1
            if a_index < len(st.session_state['chat_history']):
                st.markdown(f"**Q{i+1}:** {st.session_state['chat_history'][q_index]['message']}")
                st.markdown(f"**A:** {st.session_state['chat_history'][a_index]['message']}")
                st.markdown("---")

        if st.button("Start New Assessment"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

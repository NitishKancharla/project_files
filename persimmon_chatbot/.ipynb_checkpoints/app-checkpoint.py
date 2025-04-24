
import streamlit as st
import agents
import utils
import graph
import uuid
import os
import logging
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import queue
import numpy as np
from langgraph.graph import StateGraph

# Setup logging
logging.basicConfig(filename='persimmon.log', level=logging.INFO)

# Initialize session state
if 'stage' not in st.session_state:
    st.session_state.stage = 'upload'
    st.session_state.match_score = None
    st.session_state.questions = []
    st.session_state.current_question = None
    st.session_state.answers = []
    st.session_state.feedback = None
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.resume_buffer = None
    st.session_state.audio_queue = queue.Queue()
if 'graph' not in st.session_state:
    st.session_state.graph = graph.build_graph()

st.title("Persimmon Chatbot - Job Portal")

# Use graph and audio queue from session state
workflow = st.session_state.graph
audio_queue = st.session_state.audio_queue

def audio_frame_callback(frame: av.AudioFrame) -> av.AudioFrame:
    try:
        audio_data = frame.to_ndarray()
        logging.info(f"Received audio frame, shape: {audio_data.shape}")
        audio_queue.put(audio_data)
    except Exception as e:
        logging.error(f"Audio frame callback error: {e}")
    return frame

# Synchronous wrapper for LangGraph invoke
def run_workflow(state, action):
    try:
        state['action'] = action
        # Manually invoke the correct agent based on action
        agents_map = {
            'jd_matching': agents.JDMatchingAgent().execute,
            'store_resume_text': agents.StateAgent().execute,
            'get_resume_text': agents.StateAgent().execute,
            'generate_question': agents.InterviewAgent().execute,
            'process_answer': agents.InterviewAgent().execute,
            'generate_feedback': agents.FeedbackAgent().execute
        }
        if action == 'jd_matching':
            # Start from resume_extraction
            return workflow.invoke(state)
        elif action in agents_map:
            # Directly invoke the agent
            return agents_map[action](state)
        else:
            raise ValueError(f"Invalid action: {action}")
    except Exception as e:
        logging.error(f"LangGraph invoke error: {e}")
        raise RuntimeError(f"Failed to invoke LangGraph workflow: {str(e)}")

# Stage: Resume and JD Upload
if st.session_state.stage == 'upload':
    st.header("Upload Resume and Job Description")
    st.write(f"Debug: Session ID = {st.session_state.session_id}")
    resume_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
    jd_text = st.text_area("Enter Job Description")
    if st.button("Submit"):
        if resume_file and jd_text:
            # Save resume buffer
            st.session_state.resume_buffer = resume_file.getbuffer()
            resume_path = f"temp_{st.session_state.session_id}.pdf"
            try:
                with open(resume_path, "wb") as f:
                    f.write(st.session_state.resume_buffer)
                
                # Run graph for resume extraction and JD matching
                state = {
                    'session_id': st.session_state.session_id,
                    'resume_path': resume_path,
                    'jd_text': jd_text,
                    'resume_text': '',
                    'match_score': 0.0,
                    'questions': [],
                    'answers': [],
                    'current_question': '',
                    'feedback': '',
                    'action': 'jd_matching'
                }
                result = run_workflow(state, 'jd_matching')
                st.session_state.match_score = result['match_score']
                st.session_state.stage = 'match_result'
                
                # Clean up
                os.remove(resume_path)
            except Exception as e:
                st.error(f"An error occurred while processing the resume: {str(e)}")
                logging.error(f"Resume processing error: {e}")
                if os.path.exists(resume_path):
                    os.remove(resume_path)
                st.stop()
        else:
            st.error("Please upload a resume and enter a job description.")

# Stage: Display Match Score
if st.session_state.stage == 'match_result':
    st.header("Resume Match Result")
    st.write(f"Match Score: {st.session_state.match_score}%")
    st.write(f"Debug: Session ID = {st.session_state.session_id}")
    if st.session_state.match_score > 50:
        st.success("You are eligible for the first round!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Proceed to Interview"):
                try:
                    state = {
                        'session_id': st.session_state.session_id,
                        'resume_text': '',
                        'questions': [],
                        'answers': [],
                        'current_question': '',
                        'action': 'get_resume_text'
                    }
                    result = run_workflow(state, 'get_resume_text')
                    resume_text = result['resume_text']
                    st.write(f"Debug: Retrieved resume text length = {len(resume_text)}")
                    if not resume_text:
                        # Fallback: Re-extract from stored resume buffer
                        if st.session_state.resume_buffer:
                            resume_path = f"temp_retry_{st.session_state.session_id}.pdf"
                            with open(resume_path, "wb") as f:
                                f.write(st.session_state.resume_buffer)
                            state = {
                                'session_id': st.session_state.session_id,
                                'resume_path': resume_path,
                                'resume_text': '',
                                'action': 'store_resume_text'
                            }
                            result = run_workflow(state, 'store_resume_text')
                            resume_text = result['resume_text']
                            os.remove(resume_path)
                            if not resume_text or resume_text == "Error extracting text from PDF":
                                st.error("Failed to re-extract resume text. Please upload the resume again.")
                                logging.error(f"Resume text re-extraction failed for session_id: {st.session_state.session_id}")
                                st.session_state.stage = 'upload'
                                st.stop()
                        else:
                            st.error("Resume buffer not found. Please upload the resume again.")
                            logging.error(f"Resume buffer missing for session_id: {st.session_state.session_id}")
                            st.session_state.stage = 'upload'
                            st.stop()
                    state = {
                        'resume_text': resume_text,
                        'questions': [],
                        'answers': [],
                        'action': 'generate_question'
                    }
                    result = run_workflow(state, 'generate_question')
                    question = result['current_question']
                    st.session_state.questions.append(question)
                    st.session_state.current_question = question
                    st.session_state.stage = 'interview'
                except Exception as e:
                    st.error(f"An error occurred while starting the interview: {str(e)}")
                    logging.error(f"Interview initiation error: {e}")
                    st.stop()
        with col2:
            if st.button("Stop"):
                st.session_state.stage = 'end'
    else:
        st.error("Sorry, your resume does not meet the eligibility criteria (Match Score > 50).")
        if st.button("End Process"):
            st.session_state.stage = 'end'

# Stage: Interview
if st.session_state.stage == 'interview':
    st.header("Resume-Based Interview")
    st.write(f"Debug: Session ID = {st.session_state.session_id}")
    st.write(f"Question {len(st.session_state.questions)}: {st.session_state.current_question}")
    st.info("Click 'Start Recording' to answer, and 'Stop Recording' when done.")
    
    # WebRTC audio streamer
    webrtc_ctx = webrtc_streamer(
        key=f"audio_{len(st.session_state.questions)}",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=4096,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        media_stream_constraints={"audio": {"sampleRate": 16000, "channelCount": 1}, "video": False},
        audio_frame_callback=audio_frame_callback
    )
    
    if webrtc_ctx.state.playing:
        st.write("Recording... Click 'Stop Recording' to finish.")
    
    # Fallback audio upload
    audio_file = st.file_uploader("Or upload an audio file (if recording fails)", type=["wav", "mp3"], key=f"fallback_audio_{len(st.session_state.questions)}")
    
    if st.button("Stop Recording", key=f"stop_{len(st.session_state.questions)}") or audio_file:
        try:
            if audio_file:
                # Process uploaded audio file
                audio_path = f"temp_answer_{st.session_state.session_id}_{len(st.session_state.questions)}.wav"
                with open(audio_path, "wb") as f:
                    f.write(audio_file.getbuffer())
            else:
                # Process WebRTC audio
                audio_data = []
                while not audio_queue.empty():
                    audio_data.append(audio_queue.get())
                if audio_data:
                    audio_data = np.concatenate(audio_data, axis=0)
                    audio_path = f"temp_answer_{st.session_state.session_id}_{len(st.session_state.questions)}.wav"
                    utils.save_audio(audio_path, audio_data, sample_rate=16000)
                else:
                    st.error("No audio recorded via microphone. Please try again or upload an audio file.")
                    logging.error(f"No audio data in queue for session_id: {st.session_state.session_id}")
                    st.stop()
            
            # Process answer
            state = {
                'session_id': st.session_state.session_id,
                'audio_path': audio_path,
                'question': st.session_state.current_question,
                'answers': st.session_state.answers,
                'action': 'process_answer'
            }
            result = run_workflow(state, 'process_answer')
            answer_text = result['answers'][-1]
            st.session_state.answers.append(answer_text)
            st.write(f"Your Answer: {answer_text}")
            
            # Check if interview should continue
            if len(st.session_state.questions) < 3:  # Limit to 3 questions
                state = {
                    'session_id': st.session_state.session_id,
                    'action': 'get_resume_text'
                }
                result = run_workflow(state, 'get_resume_text')
                resume_text = result['resume_text']
                st.write(f"Debug: Retrieved resume text length for next question = {len(resume_text)}")
                if not resume_text:
                    # Fallback: Re-extract from stored resume buffer
                    if st.session_state.resume_buffer:
                        resume_path = f"temp_retry_{st.session_state.session_id}.pdf"
                        with open(resume_path, "wb") as f:
                            f.write(st.session_state.resume_buffer)
                        state = {
                            'session_id': st.session_state.session_id,
                            'resume_path': resume_path,
                            'resume_text': '',
                            'action': 'store_resume_text'
                        }
                        result = run_workflow(state, 'store_resume_text')
                        resume_text = result['resume_text']
                        os.remove(resume_path)
                        if not resume_text or resume_text == "Error extracting text from PDF":
                            st.error("Failed to re-extract resume text for next question. Please upload the resume again.")
                            logging.error(f"Resume text re-extraction failed for next question, session_id: {st.session_state.session_id}")
                            st.session_state.stage = 'upload'
                            st.stop()
                    else:
                        st.error("Resume buffer not found for next question. Please upload the resume again.")
                        logging.error(f"Resume buffer missing for next question, session_id: {st.session_state.session_id}")
                        st.session_state.stage = 'upload'
                        st.stop()
                state = {
                    'resume_text': resume_text,
                    'answers': st.session_state.answers,
                    'questions': st.session_state.questions,
                    'action': 'generate_question'
                }
                result = run_workflow(state, 'generate_question')
                question = result['current_question']
                st.session_state.questions.append(question)
                st.session_state.current_question = question
            else:
                # Generate feedback
                state = {
                    'questions': st.session_state.questions,
                    'answers': st.session_state.answers,
                    'action': 'generate_feedback'
                }
                result = run_workflow(state, 'generate_feedback')
                st.session_state.feedback = result['feedback']
                st.session_state.stage = 'feedback'
            
            # Clean up
            os.remove(audio_path)
            # Clear audio queue
            st.session_state.audio_queue = queue.Queue()
            st.rerun()
        except Exception as e:
            st.error(f"An error occurred while processing the audio: {str(e)}")
            logging.error(f"Audio processing error: {e}")
            if os.path.exists(audio_path):
                os.remove(audio_path)
            st.stop()

# Stage: Feedback
if st.session_state.stage == 'feedback':
    st.header("Interview Feedback")
    st.write(st.session_state.feedback)
    if st.button("End Process"):
        st.session_state.stage = 'end'

# Stage: End
if st.session_state.stage == 'end':
    st.header("Process Completed")
    st.write("Thank you for using Persimmon Chatbot!")
    if st.button("Restart"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

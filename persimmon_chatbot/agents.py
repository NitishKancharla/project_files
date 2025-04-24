
import utils
import logging

# Setup logging
logging.basicConfig(filename='persimmon.log', level=logging.INFO)

class Agent:
    def __init__(self, name):
        self.name = name

    def execute(self, state):
        raise NotImplementedError

class ResumeExtractionAgent(Agent):
    def __init__(self):
        super().__init__("ResumeExtractionAgent")

    def execute(self, state):
        resume_path = state['resume_path']
        resume_text = utils.extract_resume_text(resume_path)
        if resume_text == "Error extracting text from PDF":
            logging.error(f"Resume extraction failed for path: {resume_path}")
        state['resume_text'] = resume_text
        return state

class JDMatchingAgent(Agent):
    def __init__(self):
        super().__init__("JDMatchingAgent")

    def execute(self, state):
        resume_text = state['resume_text']
        jd_text = state['jd_text']
        if resume_text == "Error extracting text from PDF":
            logging.error("JD matching skipped due to invalid resume text")
            state['match_score'] = 0
        else:
            state['match_score'] = utils.compute_match_score(resume_text, jd_text)
        return state

class InterviewAgent(Agent):
    def __init__(self):
        super().__init__("InterviewAgent")

    def execute(self, state):
        if 'audio_path' in state:  # Process answer
            answer_text = utils.transcribe_audio(state['audio_path'])
            state['answers'].append(answer_text)
        else:  # Generate question
            resume_text = state['resume_text']
            previous_answers = state.get('answers', [])
            if not resume_text:
                logging.error("Cannot generate question due to empty resume text")
                state['current_question'] = "Error: Empty resume text"
            else:
                state['current_question'] = utils.generate_interview_question(resume_text, previous_answers)
        return state

class FeedbackAgent(Agent):
    def __init__(self):
        super().__init__("FeedbackAgent")

    def execute(self, state):
        questions = state['questions']
        answers = state['answers']
        state['feedback'] = utils.generate_feedback(questions, answers)
        return state

class StateAgent(Agent):
    def __init__(self):
        super().__init__("StateAgent")

    def execute(self, state):
        session_id = state['session_id']
        if 'resume_text' in state:
            # Store resume text
            utils.store_state(session_id, {'resume_text': state['resume_text']})
            logging.info(f"Stored resume text for session_id: {session_id}, length: {len(state['resume_text'])}")
        else:
            # Retrieve resume text
            stored_state = utils.retrieve_state(session_id)
            state['resume_text'] = stored_state.get('resume_text', '')
            logging.info(f"Retrieved resume text for session_id: {session_id}, length: {len(state['resume_text'])}")
        return state

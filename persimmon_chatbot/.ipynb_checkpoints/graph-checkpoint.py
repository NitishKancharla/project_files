
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, Any
import agents
import logging

# Setup logging
logging.basicConfig(filename='persimmon.log', level=logging.INFO)

class InterviewState(TypedDict):
    session_id: str
    resume_path: str
    jd_text: str
    resume_text: str
    match_score: float
    questions: list
    answers: list
    current_question: str
    audio_path: str
    feedback: str
    action: str  # For node selection in app.py

def build_graph():
    workflow = StateGraph(InterviewState)

    # Initialize agents
    resume_extraction_agent = agents.ResumeExtractionAgent()
    jd_matching_agent = agents.JDMatchingAgent()
    interview_agent = agents.InterviewAgent()
    feedback_agent = agents.FeedbackAgent()
    state_agent = agents.StateAgent()

    # Define nodes
    workflow.add_node("resume_extraction", resume_extraction_agent.execute)
    workflow.add_node("jd_matching", jd_matching_agent.execute)
    workflow.add_node("store_resume_text", state_agent.execute)
    workflow.add_node("get_resume_text", state_agent.execute)
    workflow.add_node("generate_question", interview_agent.execute)
    workflow.add_node("process_answer", interview_agent.execute)
    workflow.add_node("generate_feedback", feedback_agent.execute)

    # Define edges (minimal to ensure reachability)
    workflow.add_edge("resume_extraction", "jd_matching")
    workflow.add_edge("jd_matching", END)
    workflow.add_edge("store_resume_text", END)
    workflow.add_edge("get_resume_text", END)
    workflow.add_edge("generate_question", END)
    workflow.add_edge("process_answer", END)
    workflow.add_edge("generate_feedback", END)

    # Set entry point
    workflow.set_entry_point("resume_extraction")

    # Log graph structure
    logging.info(f"Graph nodes: {workflow.nodes.keys()}")
    logging.info(f"Graph edges: {workflow.edges}")

    # Compile the graph
    return workflow.compile()

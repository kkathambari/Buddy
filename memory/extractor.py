import threading
import re
from ai.gateway.broker import AIGateway
from core.logging import setup_logger
from memory.extractors.profile import extract_profile
from memory.extractors.learning import extract_learning
from memory.extractors.career import extract_career
from memory.extractors.projects import extract_projects
from memory.extractors.preferences import extract_preferences

logger = setup_logger("memory_extractor_coordinator")

def get_importance_score(chat_input: str) -> float:
    """Uses LLM to evaluate the importance score of a user statement (0.0 to 1.0)."""
    prompt = f"""
Evaluate the informational importance of the user's input from 0.0 to 1.0.
High importance (0.7 to 1.0) is for statements revealing permanent details about the user (name, timezone, favorite language, goals, internships, completed projects, exam study updates).
Low importance (0.0 to 0.3) is for greetings, chitchat, simple one-off questions (e.g. "hi", "how are you", "what is python").

User Chat Input:
"{chat_input}"

Return ONLY a float number between 0.0 and 1.0. Do not include any explanation.
"""
    try:
        response = AIGateway.generate_response(prompt).strip()
        match = re.search(r'\d+\.\d+|\d+', response)
        if match:
            return float(match.group(0))
    except Exception:
        pass
    return 0.5 # Default fallback

def _async_extraction_job(chat_input: str) -> None:
    logger.info(f"Running extractors for: '{chat_input[:40]}...'")
    try:
        extract_profile(chat_input)
        extract_learning(chat_input)
        extract_career(chat_input)
        extract_projects(chat_input)
        extract_preferences(chat_input)
    except Exception as e:
        logger.error(f"Error during async memory extraction: {e}")

def evaluate_and_extract(chat_input: str) -> float:
    """Evaluates the input's importance score and runs extractors asynchronously if high."""
    score = get_importance_score(chat_input)
    logger.info(f"Evaluated input importance score: {score}")
    
    if score >= 0.7:
        threading.Thread(target=_async_extraction_job, args=(chat_input,), daemon=True).start()
        
    return score

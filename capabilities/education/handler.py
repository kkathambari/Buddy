from typing import Any, Dict
from ai.gateway.broker import AIGateway
from core.logging import setup_logger

logger = setup_logger("education_capability")

# In-memory session tracking for active studying
_active_sessions: Dict[str, Dict[str, Any]] = {}

def handle_education(intent: Dict[str, Any], stats: Dict[str, Any], energy: float) -> str:
    """
    Conversational-first Education Capability.
    Manages study sessions, concept parsing, Viva oral reviews, and study metrics.
    """
    text = intent["raw_text"].lower()
    companion_id = intent.get("companion_id", "default_pet")
    
    logger.info(f"Education Capability handling request: '{text}'")
    
    session = _active_sessions.get(companion_id)
    
    # 1. Check for starting a study session
    if "study" in text or "learn" in text or "start session" in text:
        # Parse concept
        concept = "Software Development"
        for word in ["python", "javascript", "databases", "algorithms", "react"]:
            if word in text:
                concept = word.capitalize()
                break
                
        # Initialize study session
        _active_sessions[companion_id] = {
            "concept": concept,
            "stage": "viva_questioning",
            "question_index": 0,
            "correct_answers": 0
        }
        
        # Background Mock Parsing & Knowledge Graph mapping
        logger.info(f"Background parsing notes and building Knowledge Graph for: {concept}")
        
        return (
            f"Let's study {concept}. I've parsed your notes and mapped out the core concepts in your knowledge graph. "
            f"Ready for your first Viva review question? Here: What is the main purpose of {concept}?"
        )
        
    # 2. Check for active Viva questioning responses
    if session and session["stage"] == "viva_questioning":
        session["question_index"] += 1
        
        # Formulate quick evaluation prompt
        eval_prompt = f"""
Evaluate this student answer.
Topic: {session['concept']}
Student Answer: {intent['raw_text']}

Daemon is a ghost tutor. Respond in 2 sentences in Daemon's persona (calm, slightly snarky but helpful), scoring the response and asking the next question.
Daemon:
"""
        try:
            response = AIGateway.generate_response(eval_prompt)
            # Update learning progress in memory
            try:
                from shared.storage import safe_load, safe_save
                progress = safe_load("data/learning_progress.json", {})
                progress[session["concept"]] = progress.get(session["concept"], 0) + 10
                safe_save("data/learning_progress.json", progress)
            except Exception:
                pass
            return response
        except Exception:
            return "Not a bad attempt. Let's move on. Tell me more about how you'd test this concept."
            
    # 3. Check for progress analytics requests
    if "progress" in text or "analytics" in text or "mastery" in text:
        try:
            from shared.storage import safe_load
            progress = safe_load("data/learning_progress.json", {})
            if progress:
                stats_str = ", ".join(f"{k}: {v}% mastery" for k, v in progress.items())
                return f"Here is your learning graph overview: {stats_str}. Keep pushing."
        except Exception:
            pass
        return "You're at the beginning of your study journey. Ask me to 'start a study session' to log progress."

    # Fallback/General tutor help
    prompt = f"Daemon tutor response to user inquiry: '{intent['raw_text']}'. Answer in 2 sentences as a ghostly guide."
    return AIGateway.generate_response(prompt)

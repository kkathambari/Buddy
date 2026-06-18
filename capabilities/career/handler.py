from typing import Any, Dict
from ai.gateway.broker import AIGateway
from core.logging import setup_logger

logger = setup_logger("career_capability")

# In-memory session tracking for active career coaching
_active_career_sessions: Dict[str, Dict[str, Any]] = {}

def handle_career(intent: Dict[str, Any], stats: Dict[str, Any], energy: float) -> str:
    """
    Conversational-first Career Capability (JobForge).
    Manages career profiling, Resume/ATS matching, Mock Interviews, and Pet Experience scaling.
    """
    text = intent["raw_text"].lower()
    companion_id = intent.get("companion_id", "default_pet")
    
    logger.info(f"Career Capability handling request: '{text}'")
    
    session = _active_career_sessions.get(companion_id)
    
    # 1. Start career discussion / profiling
    if any(w in text for w in ["job", "internship", "career", "work", "hired"]):
        _active_career_sessions[companion_id] = {
            "stage": "profiling",
            "target_role": "Backend Developer",
            "mock_interview_stage": 0
        }
        return (
            "I'd love to help you prep for that. What kind of role or internship are we targeting? "
            "Is it backend, frontend, fullstack, or mobile?"
        )
        
    # 2. Check for active session workflow
    if session:
        stage = session["stage"]
        
        if stage == "profiling":
            # Record role
            role = "Backend Developer"
            for word in ["frontend", "backend", "fullstack", "mobile", "design"]:
                if word in text:
                    role = word.capitalize() + " Developer"
                    break
            session["target_role"] = role
            session["stage"] = "ats_review"
            
            return (
                f"Got it, {role}. Paste your resume summary here, and I'll run a quick "
                f"mock ATS scan to see how we match up."
            )
            
        elif stage == "ats_review":
            session["stage"] = "mock_interview"
            
            # Simple keyword matching for ATS score
            score = 65
            if any(w in text for w in ["python", "react", "sql", "git", "api"]):
                score += 20
                
            # Gain XP for Companion (Milestone Link)
            try:
                from shared.storage import safe_load, safe_save
                soul = safe_load("data/soul.json", {})
                soul["experience"] = soul.get("experience", 0) + 15
                safe_save("data/soul.json", soul)
                logger.info(f"XP Gained: Companion experience increased to {soul['experience']}")
            except Exception:
                pass
                
            return (
                f"I've run the ATS matching algorithm. Your score is {score}%. "
                f"You've unlocked +15 XP for Daemon! Let's do a quick mock interview practice. "
                f"First question: Tell me about a time you solved a complex bug in Python or Javascript."
            )
            
        elif stage == "mock_interview":
            # Evaluate interview answer using LLM
            eval_prompt = f"""
Evaluate this student's mock interview response.
Target Role: {session['target_role']}
Question: Tell me about a time you solved a complex bug.
Candidate Answer: {intent['raw_text']}

Daemon is a ghostly developer coach. Respond in 2 sentences. Give a quick critique and offer constructive tips.
Daemon:
"""
            try:
                response = AIGateway.generate_response(eval_prompt)
                # Clear session once interview complete
                _active_career_sessions[companion_id] = {
                    "stage": "complete",
                    "target_role": session["target_role"]
                }
                return response + " That completes our quick practice session. Keep refining!"
            except Exception:
                return "Good answer. Focus on describing the exact actions you took. Practice complete."
                
    # Default helper
    prompt = f"Daemon career coach response to user inquiry: '{intent['raw_text']}'. Answer in 2 sentences in character."
    return AIGateway.generate_response(prompt)

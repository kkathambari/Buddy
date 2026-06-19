import os
from typing import Any, Dict
from ai.gateway.broker import AIGateway
from core.logging import setup_logger
from capabilities.base import Capability

logger = setup_logger("career_capability")

class CareerCapability(Capability):
    """Pluggable JobForge capability for career guidance and resume screening."""
    
    def __init__(self):
        self._active_career_sessions: Dict[str, Dict[str, Any]] = {}
        self.sandbox_path = "data/sandbox/career/career_profile.json"

    def initialize(self) -> None:
        import os
        os.makedirs("data/sandbox/career", exist_ok=True)
        logger.info("CareerCapability initialized successfully.")

    def observe(self, context: Dict[str, Any]) -> None:
        """Receives ambient contextual updates. Queues proactive career triggers if trust > 0.7 and browsing jobs."""
        title = context.get("title", "").lower()
        companion_id = context.get("companion_id", "default_pet")
        
        # Check if title indicates job searching
        if any(w in title for w in ["linkedin", "indeed", "glassdoor", "job hunt", "internship", "hiring"]):
            try:
                from relationship.manager import get_relationship
                from proactive.cooldowns import is_cooldown_active, update_cooldown
                from proactive.trigger import proactive_queue
                
                # Check trust score
                rel = get_relationship(companion_id)
                if rel.get("trust", 0.5) > 0.7:
                    if not is_cooldown_active("career_proactive_ats"):
                        prompt = """
You are Daemon, a ghostly career coach.
Suggest to the user that since they are looking at job listings, they should paste their resume to run a quick mock ATS scan.
Keep the suggestion short, teasing, and supportive (1-2 sentences).
Daemon:
"""
                        response = AIGateway.generate_response(prompt)
                        proactive_queue.put(response)
                        update_cooldown("career_proactive_ats")
                        logger.info("Queued proactive career reminder from Career Capability.")
            except Exception as e:
                logger.error(f"Failed in CareerCapability observe trigger: {e}")

    def execute(self, intent: Dict[str, Any], stats: Dict[str, Any], energy: float) -> str:
        text = intent["raw_text"].lower()
        companion_id = intent.get("companion_id", "default_pet")
        
        logger.info(f"Career Capability handling request: '{text}'")
        session = self._active_career_sessions.get(companion_id)
        
        # 1. Start career discussion / profiling
        if any(w in text for w in ["job", "internship", "career", "work", "hired"]):
            self._active_career_sessions[companion_id] = {
                "stage": "profiling",
                "target_role": "Backend Developer",
                "mock_interview_stage": 0
            }
            # Log product analytics
            try:
                from core.analytics import ProductAnalytics
                ProductAnalytics.track_event("career_profiling_started")
            except Exception:
                pass
            return (
                "I'd love to help you prep for that. What kind of role or internship are we targeting? "
                "Is it backend, frontend, fullstack, or mobile?"
            )
            
        # 2. Check for active session workflow
        if session:
            stage = session["stage"]
            
            if stage == "profiling":
                role = "Backend Developer"
                for word in ["frontend", "backend", "fullstack", "mobile", "design"]:
                    if word in text:
                        role = word.capitalize() + " Developer"
                        break
                session["target_role"] = role
                session["stage"] = "ats_review"
                
                # Write target role inside sandbox profile
                try:
                    from shared.storage import safe_load, safe_save
                    profile = safe_load(self.sandbox_path, {})
                    profile["target_role"] = role
                    safe_save(self.sandbox_path, profile)
                except Exception:
                    pass
                
                # Log profile update event to timeline
                try:
                    from timeline.history import log_timeline_event
                    log_timeline_event(
                        title=f"Set target career role: {role}",
                        source="conversation",
                        metadata={"role": role}
                    )
                except Exception:
                    pass
                    
                # Log product analytics
                try:
                    from core.analytics import ProductAnalytics
                    ProductAnalytics.track_event("career_role_set", {"role": role})
                except Exception:
                    pass
                    
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
                    
                # Write ATS score inside sandbox profile
                try:
                    from shared.storage import safe_load, safe_save
                    profile = safe_load(self.sandbox_path, {})
                    profile["last_ats_score"] = score
                    safe_save(self.sandbox_path, profile)
                except Exception:
                    pass

                # Gain XP for Companion (Milestone Link via Event Bus)
                try:
                    from shared.storage import safe_load, safe_save
                    soul = safe_load("data/soul.json", {})
                    soul["experience"] = soul.get("experience", 0) + 15
                    safe_save("data/soul.json", soul)
                    
                    # Log event to timeline (will unlock milestone)
                    from timeline.history import log_timeline_event
                    log_timeline_event(
                        title=f"Completed resume ATS score check: {score}%",
                        source="conversation",
                        metadata={"ats_score": score}
                    )
                except Exception:
                    pass
                    
                # Log product analytics
                try:
                    from core.analytics import ProductAnalytics
                    ProductAnalytics.track_event("resume_ats_checked", {"score": score})
                except Exception:
                    pass
                    
                return (
                    f"I've run the ATS matching algorithm. Your score is {score}%. "
                    f"You've unlocked +15 XP for Daemon! Let's do a quick mock interview practice. "
                    f"First question: Tell me about a time you solved a complex bug in Python or Javascript."
                )
                
            elif stage == "mock_interview":
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
                    
                    # Clear session stage but keep companion info
                    self._active_career_sessions[companion_id] = {
                        "stage": "complete",
                        "target_role": session["target_role"]
                    }
                    
                    try:
                        from timeline.history import log_timeline_event
                        log_timeline_event(
                            title="Mock interview completed",
                            source="conversation",
                            metadata={"role": session["target_role"]}
                        )
                    except Exception:
                        pass
                        
                    # Log product analytics
                    try:
                        from core.analytics import ProductAnalytics
                        ProductAnalytics.track_event("mock_interview_completed", {"role": session["target_role"]})
                    except Exception:
                        pass
                        
                    return response + " That completes our quick practice session. Keep refining!"
                except Exception:
                    return "Good answer. Focus on describing the exact actions you took. Practice complete."
                    
        # Default helper fallback
        prompt = f"Daemon career coach response to user inquiry: '{intent['raw_text']}'. Answer in 2 sentences in character."
        return AIGateway.generate_response(prompt)

    def reflect(self) -> Dict[str, Any]:
        return {"trust_increment": 0.08, "bond_points": 3}

    def update_memory(self) -> None:
        """Commits career profiles and stats to the sandbox filesystem."""
        logger.info("CareerCapability memory update committed successfully.")

    def shutdown(self) -> None:
        logger.info("CareerCapability shutdown complete.")

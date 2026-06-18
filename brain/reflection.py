from typing import Any, Dict, Optional
from memory.conversations import load_memory
from core.logging import setup_logger

logger = setup_logger("reflection")

class SelfReflection:
    """Handles Daemon's self-reflection loop to evaluate conversational success."""

    @staticmethod
    def reflect_on_recent_chat() -> Dict[str, Any]:
        """
        Analyzes the last few turns of conversation history.
        Determines user mood shifting and if errors/problems were resolved.
        """
        history = load_memory()
        if not history:
            return {"status": "no_data", "success_score": 0.5}

        logger.info("Daemon is running self-reflection on conversation logs.")

        recent_turns = history[-3:]
        user_sentiment = 0.5  # Neutral default
        success = False

        for turn in recent_turns:
            user_text = turn.get("user", "").lower()
            # Check for success indicators
            if any(w in user_text for w in ["thank", "thanks", "solved", "fixed", "worked", "working", "awesome", "perfect"]):
                success = True
                user_sentiment += 0.2
            elif any(w in user_text for w in ["still error", "not working", "broken", "failed", "sucks", "bad"]):
                user_sentiment -= 0.2

        # Clamp sentiment
        user_sentiment = min(1.0, max(0.0, user_sentiment))

        reflection_summary = {
            "status": "success" if success else "ongoing",
            "success_score": user_sentiment,
            "resolved_last_problem": success
        }
        
        logger.info(f"Self-reflection summary: {reflection_summary}")
        return reflection_summary

    @staticmethod
    def get_reflective_prompt(reflection: Dict[str, Any]) -> Optional[str]:
        """Generates a contextual follow-up prompt based on self-reflection results."""
        if reflection.get("resolved_last_problem"):
            return "Did I help you get that working?"
        if reflection.get("success_score", 0.5) < 0.3:
            return "You seem a bit frustrated... everything okay?"
        return None

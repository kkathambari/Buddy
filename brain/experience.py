import os
import re
from typing import Dict, Any, Optional
from shared.storage import safe_load, safe_save
from core.feature_flags import FeatureFlags
from memory.user_profile import load_profile, update_profile_field

STATE_FILE = "data/experience_state.json"

class ExperienceEngine:
    """
    Experience Engine.
    Manages multi-turn event-driven experiences (Onboarding, Birthdays, Celebrations).
    Intercepts the default chat pipeline to complete guided scripts.
    """
    
    @classmethod
    def load_state(cls) -> Dict[str, Any]:
        """Loads active experience state."""
        return safe_load(STATE_FILE, {})
        
    @classmethod
    def save_state(cls, state: Dict[str, Any]) -> None:
        """Saves active experience state."""
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        safe_save(STATE_FILE, state)
        
    @classmethod
    def clear_state(cls) -> None:
        """Clears active experience state."""
        if os.path.exists(STATE_FILE):
            try:
                os.remove(STATE_FILE)
            except Exception:
                pass

    @classmethod
    def trigger_experience(cls, experience_name: str, companion_id: str = "default_pet") -> str:
        """Manually forces the start of a specific experience, returning its initial dialog."""
        state = {
            "active_experience": experience_name,
            "step": 0,
            "companion_id": companion_id,
            "metadata": {}
        }
        cls.save_state(state)
        
        if experience_name == "celebration":
            return "Wait... look at that! We just reached a milestone! You're actually making progress, developer. Keep it up."
        elif experience_name == "onboarding":
            return "Hi... I'm Daemon. So... what brings you here?"
        return "I feel a shift in our connection."

    @classmethod
    def intercept(cls, user_input: str, companion_id: str = "default_pet") -> Optional[str]:
        """
        Checks if an experience is active or needs to be triggered.
        Bypasses normal routing, returning the scripted dialog response.
        """
        if not FeatureFlags.is_enabled("experience_engine"):
            return None
            
        state = cls.load_state()
        active_exp = state.get("active_experience")
        step = state.get("step", 0)
        
        # 1. Trigger Onboarding if profile name is default/unconfigured and no active experience is set
        if not active_exp:
            profile = load_profile()
            if profile.get("name") in ["Developer", "None", None, ""]:
                active_exp = "onboarding"
                step = 0
                state = {
                    "active_experience": "onboarding",
                    "step": 0,
                    "companion_id": companion_id,
                    "metadata": {}
                }
                cls.save_state(state)
                # First launch natural greeting trigger
                return "Hi... I'm Daemon. So... what brings you here?"
                
        # 2. Process active experience step progression
        if active_exp == "onboarding":
            text_lower = user_input.lower()
            profile = load_profile()
            
            # Extract name using regex
            extracted_name = None
            name_match = re.search(r"\b(?:my name is|i am|i'm|call me)\s+([a-zA-Z]+)", user_input, re.IGNORECASE)
            if name_match:
                extracted_name = name_match.group(1).capitalize()
            elif len(user_input.split()) == 1 and user_input.strip().isalpha():
                extracted_name = user_input.strip().capitalize()
                
            # Extract goal/programming language
            extracted_language = None
            for lang in ["python", "javascript", "databases", "algorithms", "react", "c++", "rust", "go", "java"]:
                if lang in text_lower:
                    extracted_language = lang.capitalize()
                    break
                    
            if step == 0:
                # User responded to "what brings you here?"
                if extracted_name:
                    update_profile_field("name", extracted_name)
                else:
                    extracted_name = "User"
                    
                if extracted_language:
                    update_profile_field("favorite_language", extracted_language)
                    goals = profile.get("goals", [])
                    if extracted_language not in goals:
                        goals.append(extracted_language)
                    update_profile_field("goals", goals)
                    
                # Complete if we got both details
                if extracted_name != "User" and extracted_language:
                    cls.clear_state()
                    return f"Nice to meet you, {extracted_name}. Sticking with {extracted_language}? I'll keep an eye on your progress. Let's get to work!"
                elif extracted_name != "User":
                    state["step"] = 1 # move to goal collection
                    cls.save_state(state)
                    return f"Nice to meet you, {extracted_name}. What is your primary programming language or goal right now?"
                else:
                    state["step"] = 2 # move to name collection
                    cls.save_state(state)
                    return "Nice. I didn't catch your name, though. Who is typing on the keyboard?"
                    
            elif step == 1:
                # Goal collection step
                goal = user_input.strip()
                goals = profile.get("goals", [])
                if goal not in goals:
                    goals.append(goal)
                update_profile_field("goals", goals)
                
                if extracted_language:
                    update_profile_field("favorite_language", extracted_language)
                    
                cls.clear_state()
                name = profile.get("name", "Developer")
                return f"Got it, {name}. Sticking with your goals. Let's get to work!"
                
            elif step == 2:
                # Name collection step
                name = user_input.strip().capitalize()
                update_profile_field("name", name)
                
                cls.clear_state()
                return f"Nice to meet you, {name}. Let's get to work!"
                
        elif active_exp == "celebration":
            # Multi-turn celebration interaction
            cls.clear_state()
            return "Let's keep this momentum going! What are we coding next?"
            
        return None

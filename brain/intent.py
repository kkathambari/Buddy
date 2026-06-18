from typing import Any, Dict
from brain.tone import analyze_tone
from brain.emotion import detect_emotion

class IntentParser:
    """Parses user input to classify dialog intents (chat, coding aid, study sessions, career prep)."""
    
    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        
        # Default intent
        intent = {
            "category": "general_chat",
            "capability": None,
            "tone": analyze_tone(text),
            "emotion": detect_emotion(text),
            "raw_text": text
        }
        
        # Rule-based capability routing
        if any(w in text_lower for w in ["study", "learn", "exam", "quiz", "revision", "viva", "concept"]):
            intent["category"] = "capability_execution"
            intent["capability"] = "education"
        elif any(w in text_lower for w in ["job", "career", "interview", "resume", "internship", "ats"]):
            intent["category"] = "capability_execution"
            intent["capability"] = "career"
        elif any(w in text_lower for w in ["code", "bug", "compile", "script", "refactor", "exception"]):
            intent["category"] = "capability_execution"
            intent["capability"] = "coding"
        elif any(w in text_lower for w in ["todo", "schedule", "plan", "calendar"]):
            intent["category"] = "capability_execution"
            intent["capability"] = "planner"
            
        return intent

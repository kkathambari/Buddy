from typing import Any, Dict
from brain.intent_types import Intent, IntentCategory
from brain.intent_rules import match_intent_rules

def detect_intent(message: str) -> Intent:
    """
    Detects the user's intent with zero LLM latency.
    Parses input against rule matrices to categorize dialogue context.
    """
    return match_intent_rules(message)

class IntentParser:
    """
    Backward-compatibility wrapper.
    Converts the new structured Intent object into the old dictionary payload.
    """
    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        intent_obj = detect_intent(text)
        
        # Resolve capabilities
        capability = None
        category = "general_chat"
        if intent_obj.category == IntentCategory.LEARNING:
            capability = "education"
            category = "capability_execution"
        elif intent_obj.category == IntentCategory.CAREER:
            capability = "career"
            category = "capability_execution"
            
        from brain.tone import analyze_tone
        from brain.emotion import detect_emotion
        
        return {
            "category": category,
            "capability": capability,
            "tone": analyze_tone(text),
            "emotion": detect_emotion(text),
            "raw_text": text
        }

import random
from typing import Any, Dict
from brain.intent_types import Intent, IntentCategory
from core.logging import setup_logger
from core.exceptions import CapabilityException
from brain.reasoner import CognitiveReasoner
from capabilities.base import Capability

logger = setup_logger("decision_engine")

class DecisionEngine:
    """
    Decision Engine (Central Brain Router).
    Evaluates parsed intent and routes execution to rule handlers, capabilities, or LLMs.
    """
    
    def __init__(self):
        self._capabilities: Dict[str, Capability] = {}
        
    def register_capability(self, name: str, capability: Capability) -> None:
        """Registers a pluggable capability handler instance."""
        if not isinstance(capability, Capability):
            raise TypeError(f"Capability must be an instance of Capability, got {type(capability)}")
        self._capabilities[name] = capability
        logger.info(f"Registered capability in Decision Engine: '{name}'")
        
    def execute(self, intent: Intent, stats: Dict[str, Any], energy: float) -> str:
        """Decides routing path and executes capability, rules, or LLM."""
        category = intent.category
        logger.info(f"Decision Engine routing category: '{category.value}'")
        
        # Convert Intent object to dictionary format for backward compatibility with handlers
        legacy_intent = {
            "category": "capability_execution" if category in [IntentCategory.LEARNING, IntentCategory.CAREER] else "general_chat",
            "capability": "education" if category == IntentCategory.LEARNING else ("career" if category == IntentCategory.CAREER else None),
            "tone": intent.entities.get("tone", {"emotion": "neutral", "intensity": "low", "hidden": False}),
            "emotion": intent.entities.get("emotion", "neutral"),
            "raw_text": intent.raw_text,
            "entities": intent.entities
        }
        
        # 1. Route to Learning capability (Education)
        if category == IntentCategory.LEARNING:
            from core.feature_flags import FeatureFlags
            if not FeatureFlags.is_enabled("education"):
                logger.info("Education capability requested but feature is disabled by flag.")
                return "The Education Capability is currently disabled."
            if "education" in self._capabilities:
                try:
                    return self._capabilities["education"].execute(legacy_intent, stats, energy)
                except Exception as e:
                    logger.error(f"Education capability failed: {e}", exc_info=True)
                    raise CapabilityException(f"Education capability failed: {e}")
            else:
                logger.warning("Education capability requested but not registered.")
                    
        # 2. Route to Career capability
        elif category == IntentCategory.CAREER:
            from core.feature_flags import FeatureFlags
            if not FeatureFlags.is_enabled("career"):
                logger.info("Career capability requested but feature is disabled by flag.")
                return "The Career Capability is currently disabled."
            if "career" in self._capabilities:
                try:
                    return self._capabilities["career"].execute(legacy_intent, stats, energy)
                except Exception as e:
                    logger.error(f"Career capability failed: {e}", exc_info=True)
                    raise CapabilityException(f"Career capability failed: {e}")
            else:
                logger.warning("Career capability requested but not registered.")
                
        # 3. Route to Productivity Queries (Rules / Metrics)
        elif category == IntentCategory.PRODUCTIVITY_QUERY:
            try:
                from memory.projects import analyze_productivity
                insights = analyze_productivity()
                return f"Here is your productivity context: {insights}"
            except Exception:
                return "I'm still gathering your activity metrics. Keep coding!"
                
        # 4. Route to System Commands
        elif category == IntentCategory.SYSTEM_COMMAND:
            # Directly returned command tags to be parsed by conversation runner
            return intent.raw_text
            
        # 5. Route to Greetings (Rules / Quick Response)
        elif category == IntentCategory.GREETING:
            greetings = [
                "Hey there. What are you building today?",
                "Hey. Ready to get some work done?",
                "Waking up... looks like you're active.",
                "Hmm... hello. Back at the keyboard?"
            ]
            return random.choice(greetings)
            
        # Default Fallback to LLM Reasoner for COMPANIONSHIP and fuzzy matches
        logger.info("Executing core Cognitive Reasoner loop.")
        return CognitiveReasoner.reason(legacy_intent, stats, energy)

# Global singleton Decision Engine instance
global_decision_engine = DecisionEngine()

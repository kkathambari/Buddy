from typing import Any, Dict, Callable, Optional
from core.logging import setup_logger
from core.exceptions import CapabilityException
from brain.reasoner import CognitiveReasoner

logger = setup_logger("capability_router")

class CapabilityRouter:
    """
    Capability Router.
    Routes parsed user intents to registered capability modules (e.g., Education, Career).
    If no capability matches or is registered, defaults to standard Cognitive Reasoner.
    """
    def __init__(self):
        self._capabilities: Dict[str, Callable[[Dict[str, Any], Dict[str, Any], float], str]] = {}

    def register_capability(self, name: str, handler: Callable[[Dict[str, Any], Dict[str, Any], float], str]) -> None:
        """Registers a capability module handler."""
        self._capabilities[name] = handler
        logger.info(f"Registered capability module: '{name}'")

    def unregister_capability(self, name: str) -> None:
        """Unregisters a capability module."""
        if name in self._capabilities:
            del self._capabilities[name]
            logger.info(f"Unregistered capability module: '{name}'")

    def route_and_execute(self, intent: Dict[str, Any], stats: Dict[str, Any], energy: float) -> str:
        """Routes the intent to the matching capability or falls back to reasoning."""
        cap_name = intent.get("capability")
        
        if cap_name and cap_name in self._capabilities:
            logger.info(f"Routing intent to capability handler: '{cap_name}'")
            try:
                # Call pluggable capability
                return self._capabilities[cap_name](intent, stats, energy)
            except Exception as e:
                logger.error(f"Capability '{cap_name}' failed to execute: {e}", exc_info=True)
                raise CapabilityException(f"Execution error in capability '{cap_name}': {e}")
                
        # Default fallback to cognitive reasoning loop
        logger.info("No capability plugin matched or registered. Executing core reasoning loop.")
        return CognitiveReasoner.reason(intent, stats, energy)

# Global router instance
global_router = CapabilityRouter()

from core.logging import setup_logger

logger = setup_logger("emotion")

class EmotionMatrix:
    """
    Emotion Matrix.
    Tracks core companion mood metrics: happiness, focus, energy, and trust.
    Limits all values strictly between 0.0 and 1.0.
    """
    def __init__(self, happiness: float = 0.5, focus: float = 0.5, energy: float = 0.5, trust: float = 0.5):
        self.happiness = self._clamp(happiness)
        self.focus = self._clamp(focus)
        self.energy = self._clamp(energy)
        self.trust = self._clamp(trust)

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))

    def update_emotional_state(self, event_type: str, delta: float = 0.1) -> None:
        """Modifies metrics based on event categories."""
        event_lower = event_type.lower()
        if "success" in event_lower or "pass" in event_lower:
            self.happiness += delta
            self.focus += delta
            self.energy += delta
            logger.info(f"Emotion updated on success event. Boosted happiness/focus/energy.")
        elif "failure" in event_lower or "fail" in event_lower:
            self.happiness -= delta
            self.focus -= delta
            self.energy -= delta
            logger.info(f"Emotion updated on failure event. Drained happiness/focus/energy.")
        elif "compliment" in event_lower or "thanks" in event_lower:
            self.trust += delta
            self.happiness += delta
            logger.info(f"Emotion updated on compliment event. Boosted trust/happiness.")
        elif "critique" in event_lower or "correction" in event_lower:
            self.trust -= delta
            self.happiness -= delta
            logger.info(f"Emotion updated on critique event. Reduced trust/happiness.")
            
        # Ensure values stay clamped
        self.happiness = self._clamp(self.happiness)
        self.focus = self._clamp(self.focus)
        self.energy = self._clamp(self.energy)
        self.trust = self._clamp(self.trust)
        
    def to_dict(self) -> dict:
        return {
            "happiness": self.happiness,
            "focus": self.focus,
            "energy": self.energy,
            "trust": self.trust
        }

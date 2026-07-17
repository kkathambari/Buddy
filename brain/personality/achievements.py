from typing import List, Dict, Any
from core.logging import setup_logger

logger = setup_logger("achievements")

class AchievementManager:
    """
    Achievement Manager.
    Tracks leveling XP thresholds, user levels, and unlocked achievement lists.
    """
    def __init__(self, level: int = 1, xp: int = 0, achievements: List[str] = None):
        self.level = level
        self.xp = xp
        self.achievements = achievements or []

    def get_xp_threshold(self) -> int:
        """Returns the XP threshold required to transition to next level."""
        return self.level * 100

    def add_xp(self, amount: int) -> bool:
        """Adds XP and triggers level-up transitions if thresholds are exceeded."""
        self.xp += amount
        leveled_up = False
        
        while self.xp >= self.get_xp_threshold():
            self.xp -= self.get_xp_threshold()
            self.level += 1
            leveled_up = True
            logger.info(f"Level up! User is now level {self.level}.")
            
        return leveled_up

    def grant_achievement(self, name: str) -> bool:
        """Unlocks achievement milestones."""
        if name not in self.achievements:
            self.achievements.append(name)
            logger.info(f"Achievement unlocked: '{name}'!")
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "xp": self.xp,
            "achievements": self.achievements
        }

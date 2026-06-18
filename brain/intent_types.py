from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict

class IntentCategory(Enum):
    GREETING = "greeting"
    COMPANIONSHIP = "companionship"
    LEARNING = "learning"
    CAREER = "career"
    EMOTION = "emotion"
    MEMORY_QUERY = "memory_query"
    PRODUCTIVITY_QUERY = "productivity_query"
    SYSTEM_COMMAND = "system_command"

@dataclass
class Intent:
    category: IntentCategory
    raw_text: str
    confidence: float = 1.0
    entities: Dict[str, Any] = field(default_factory=dict)

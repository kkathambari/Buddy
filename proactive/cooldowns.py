import time
from typing import Dict

_last_times: Dict[str, float] = {}

COOLDOWNS = {
    "active_category_changed": 600.0,  # 10 minutes
    "user_struggling": 300.0,           # 5 minutes
    "default": 300.0
}

def is_cooldown_active(event_type: str) -> bool:
    """Checks if the cooldown for a specific event type is active."""
    now = time.time()
    last_time = _last_times.get(event_type, 0.0)
    cooldown = COOLDOWNS.get(event_type, COOLDOWNS["default"])
    return (now - last_time) < cooldown

def update_cooldown(event_type: str) -> None:
    """Updates the last occurrence time for an event type to now."""
    _last_times[event_type] = time.time()

def reset_cooldown(event_type: str) -> None:
    """Resets the cooldown for an event type (useful for testing or forces)."""
    if event_type in _last_times:
        del _last_times[event_type]

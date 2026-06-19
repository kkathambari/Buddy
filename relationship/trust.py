def get_proactivity_level(trust: float) -> str:
    """
    Returns the proactivity throttle level based on the trust score.
    - Quiet: trust < 0.3
    - Moderate: 0.3 <= trust <= 0.7
    - High: trust > 0.7
    """
    if trust < 0.3:
        return "quiet"
    elif trust <= 0.7:
        return "moderate"
    else:
        return "high"

def is_proactive_allowed(trust: float, event_type: str, duration_sec: float = 0.0) -> bool:
    """
    Checks if a proactive action is allowed under the current trust level.
    - trust < 0.3: Zero proactive actions allowed.
    - trust 0.3 -> 0.7: Focus reminders allowed if coding duration is >= 2 hours (7200 seconds).
    - trust > 0.7: All proactive suggestions/quizzes are allowed.
    """
    level = get_proactivity_level(trust)
    if level == "quiet":
        return False
    elif level == "moderate":
        if event_type == "focus_reminder":
            return duration_sec >= 7200.0
        return False
    else:
        # High trust allows all triggers
        return True

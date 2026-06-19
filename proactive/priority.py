from enum import IntEnum

class ProactivePriority(IntEnum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

def get_event_priority(event_type: str) -> ProactivePriority:
    """Returns priority classification for an event type."""
    if event_type in ["focus_reminder", "exam_reminder", "study_alert"]:
        return ProactivePriority.HIGH
    elif event_type in ["milestone_unlocked", "task_completed"]:
        return ProactivePriority.MEDIUM
    else:
        return ProactivePriority.LOW

import os
from typing import List, Dict, Any
from shared.storage import safe_load, safe_save
from timeline.events import TimelineEvent

TIMELINE_FILE = "data/timeline.json"

def load_timeline() -> List[Dict[str, Any]]:
    return safe_load(TIMELINE_FILE, [])

def save_timeline(timeline: List[Dict[str, Any]]) -> None:
    safe_save(TIMELINE_FILE, timeline)

def log_timeline_event(title: str, source: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Logs a new event to the chronological timeline history."""
    event = TimelineEvent(title, source, metadata)
    timeline = load_timeline()
    event_dict = event.to_dict()
    timeline.append(event_dict)
    save_timeline(timeline)
    
    # Check if this unlocks any milestones
    try:
        from timeline.milestones import evaluate_timeline_milestones
        evaluate_timeline_milestones(event_dict)
    except Exception as e:
        # Ignore errors during milestone checks
        pass
        
    return event_dict

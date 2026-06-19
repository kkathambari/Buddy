from datetime import datetime
from typing import List, Dict, Any

def log_interaction(history_list: List[Dict[str, Any]], action: str, trust: float, bond: int) -> List[Dict[str, Any]]:
    """Logs an interaction or milestone update to the history list, keeping the last 50 entries."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "trust": round(trust, 2),
        "bond": bond
    }
    history_list.append(entry)
    # Keep history bounded
    if len(history_list) > 50:
        history_list = history_list[-50:]
    return history_list

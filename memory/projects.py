import json
import os
from datetime import datetime
from typing import Dict, List, Any

def get_productivity_file():
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app and app.user_data_dir:
            return os.path.join(app.user_data_dir, "productivity.json")
    except Exception:
        pass
    return "data/productivity.json"

def load_data():
    prod_file = get_productivity_file()
    if not os.path.exists(prod_file):
        return {"sessions": []}
    try:
        with open(prod_file, "r") as f:
            return json.load(f)
    except Exception:
        return {"sessions": []}

def save_data(data):
    prod_file = get_productivity_file()
    os.makedirs(os.path.dirname(prod_file), exist_ok=True)
    with open(prod_file, "w") as f:
        json.dump(data, f, indent=4)

def log_session(category, start_datetime, end_datetime):
    if category not in ["coding", "studying", "engagement"]:
        return # We only analyze deep work/engagement
        
    duration = (end_datetime - start_datetime).total_seconds() / 60.0
    
    # 1 minute minimum for testing/engagement, 5 minutes for work
    min_duration = 1.0 if category == "engagement" else 5.0
    if duration < min_duration:
        return
        
    data = load_data()
    data["sessions"].append({
        "category": category,
        "date": start_datetime.strftime("%Y-%m-%d"),
        "hour": start_datetime.hour,
        "duration_mins": round(duration, 2)
    })
    
    if len(data["sessions"]) > 100:
        data["sessions"] = data["sessions"][-100:]
        
    save_data(data)

def analyze_productivity():
    """
    Returns a natural language string summarizing the user's behavioral patterns.
    """
    data = load_data()
    sessions = data.get("sessions", [])
    
    if not sessions:
        return "Not enough data yet."
        
    total_time = sum(s["duration_mins"] for s in sessions)
    avg_session = total_time / len(sessions)
    
    hour_counts = {}
    for s in sessions:
        hour_counts[s["hour"]] = hour_counts.get(s["hour"], 0) + s["duration_mins"]
        
    best_hour = max(hour_counts, key=hour_counts.get)
    
    am_pm = "AM" if best_hour < 12 else "PM"
    display_hour = best_hour if best_hour <= 12 else best_hour - 12
    if display_hour == 0: display_hour = 12
    
    insight = f"User averages {int(avg_session)} minutes per session. "
    insight += f"They are most active around {display_hour} {am_pm}. "
    
    if avg_session < 15:
        insight += "User has fragmented focus. They might need help avoiding distractions."
    elif avg_session > 90:
        insight += "User works for dangerously long periods. Remind them to stretch."
        
    return insight

DECISIONS_FILE = "data/project_decisions.json"

def load_project_decisions() -> Dict[str, List[Dict[str, Any]]]:
    from shared.storage import safe_load
    return safe_load(DECISIONS_FILE, {})

def save_project_decisions(data: Dict[str, List[Dict[str, Any]]]) -> None:
    from shared.storage import safe_save
    safe_save(DECISIONS_FILE, data)

def log_project_decision(project_path: str, decision_id: str, title: str, status: str, content: str) -> None:
    """Logs an architectural design decision or project milestone."""
    data = load_project_decisions()
    if project_path not in data:
        data[project_path] = []
        
    data[project_path] = [d for d in data[project_path] if d["id"] != decision_id]
    
    data[project_path].append({
        "id": decision_id,
        "title": title,
        "status": status,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    save_project_decisions(data)

def get_project_decisions(project_path: str) -> List[Dict[str, Any]]:
    """Retrieves all logged decisions for the workspace path."""
    data = load_project_decisions()
    return data.get(project_path, [])

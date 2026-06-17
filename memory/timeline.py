from shared.storage import safe_load, safe_save
from datetime import datetime

FILE = "data/emotion_history.json"

def load_history():
    return safe_load(FILE, [])

def save_history(data):
    safe_save(FILE, data[-50:])

def log_emotion(emotion):
    history = load_history()
    history.append({
        "emotion": emotion,
        "time": str(datetime.now())
    })
    save_history(history)

def detect_pattern():
    history = load_history()

    if len(history) < 5:
        return None

    recent = [h["emotion"] for h in history[-5:]]

    if all(e == "sad" for e in recent):
        return "consistent_sad"

    if recent.count("sad") >= 3:
        return "frequent_sad"

    if recent.count("happy") >= 4:
        return "consistently_happy"

    return None

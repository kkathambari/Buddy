from datetime import datetime
from shared.storage import safe_load, safe_save

CARE_FILE = "data/care.json"

def load_last_interaction():
    return safe_load(CARE_FILE, {"last_seen": str(datetime.now())})

def update_last_interaction():
    data = {"last_seen": str(datetime.now())}
    safe_save(CARE_FILE, data)

def get_care_message():
    data = load_last_interaction()
    last = datetime.fromisoformat(data["last_seen"])
    now = datetime.now()
    hours = (now - last).total_seconds() / 3600
    if hours > 24: return "Hey... it's been a while. I was wondering where you went."
    elif hours > 6: return "You've been away for some time... everything okay?"
    else: return None

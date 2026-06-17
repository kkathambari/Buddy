from shared.storage import safe_load, safe_save

HISTORY_FILE = "data/history.json"

def log_activity(energy):
    data = safe_load(HISTORY_FILE, [])
    data.append(energy)
    safe_save(HISTORY_FILE, data[-100:])

def predict_drop():
    data = safe_load(HISTORY_FILE, [])
    if len(data) < 5: return "Not enough data"
    recent = data[-5:]
    if all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
        return "⚠ Energy dropping consistently"
    if sum(recent)/len(recent) < 30:
        return "⚠ Low productivity"
    return "Stable"

import json
import os

def safe_load(file, default):
    try:
        if not os.path.exists(file):
            return default
        with open(file, "r") as f:
            data = json.load(f)
            if isinstance(default, dict) and isinstance(data, dict):
                merged = default.copy()
                merged.update(data)
                return merged
            return data
    except Exception:
        return default

def safe_save(file, data):
    try:
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

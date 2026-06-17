from shared.storage import safe_load, safe_save

EVOLVE_FILE = "data/evolve.json"

def load_evolution():
    return safe_load(EVOLVE_FILE, {"experience": 0, "traits": {}})

def save_evolution(data):
    safe_save(EVOLVE_FILE, data)

def update_evolution(interaction=True):
    data = load_evolution()
    if interaction:
        data["experience"] += 1
    if data["experience"] > 20:
        data["traits"]["more_emotional"] = True
    if data["experience"] > 50:
        data["traits"]["more_personal"] = True
    save_evolution(data)
    return data

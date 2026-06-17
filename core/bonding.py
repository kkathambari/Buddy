from shared.storage import safe_load, safe_save

BOND_FILE = "data/bond.json"

def load_bond():
    return safe_load(BOND_FILE, {"bond": 0})

def save_bond(data):
    safe_save(BOND_FILE, data)

def update_bond(interaction=True):
    data = load_bond()
    if interaction:
        data["bond"] += 1
    else:
        data["bond"] -= 0.5
    data["bond"] = max(0, data["bond"])
    save_bond(data)
    return data["bond"]

def get_relationship_level(bond):
    if bond < 10: return "stranger"
    elif bond < 30: return "familiar"
    elif bond < 60: return "friend"
    else: return "close"

def get_attachment_style(bond):
    if bond < 10: return "neutral"
    elif bond < 40: return "warm"
    else: return "attached"

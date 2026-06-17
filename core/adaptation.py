from shared.storage import safe_load, safe_save

FILE = "data/adaptation.json"

def load_data():
    return safe_load(FILE, {
        "warmth": 0.5,
        "playfulness": 0.5,
        "depth": 0.5
    })

def save_data(data):
    safe_save(FILE, data)

def adapt_to_user(tone):
    data = load_data()

    if tone["emotion"] == "sad":
        data["warmth"] += 0.05
        data["depth"] += 0.03

    if tone["emotion"] == "happy":
        data["playfulness"] += 0.05

    # clamp values
    for k in data:
        data[k] = min(1.0, max(0.0, data[k]))

    save_data(data)
    return data

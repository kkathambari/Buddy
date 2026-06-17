from shared.storage import safe_load, safe_save

MEMORY_FILE = "data/memory.json"

def load_memory():
    return safe_load(MEMORY_FILE, [])

def save_memory(memory):
    safe_save(MEMORY_FILE, memory[-20:])

def add_memory(user, bot, emotion):
    memory = load_memory()
    memory.append({"user": user, "bot": bot, "emotion": emotion})
    save_memory(memory)

def get_context():
    memory = load_memory()
    context = ""
    for m in memory[-5:]:
        context += f"User: {m['user']}\nBuddy: {m['bot']}\n"
    return context

from shared.storage import safe_load, safe_save
from datetime import datetime
from typing import List, Dict, Any

MEMORY_FILE = "data/working_memory.json"

def load_working_memory() -> List[Dict[str, Any]]:
    return safe_load(MEMORY_FILE, [])

def save_working_memory(memory: List[Dict[str, Any]]) -> None:
    # Retain only the last 20 turns of context
    safe_save(MEMORY_FILE, memory[-20:])

def add_dialog_turn(user: str, bot: str, emotion: str) -> None:
    memory = load_working_memory()
    memory.append({
        "user": user,
        "bot": bot,
        "emotion": emotion,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_working_memory(memory)

def estimate_tokens(text: str) -> int:
    return len(text) // 4

def get_recent_context(max_tokens: int = 2000) -> str:
    memory = load_working_memory()
    context = ""
    current_tokens = 0
    
    # Iterate backwards to keep the most recent messages
    lines = []
    for m in reversed(memory):
        line = f"User: {m['user']}\nBuddy: {m['bot']}\n"
        tokens = estimate_tokens(line)
        if current_tokens + tokens > max_tokens:
            break
        lines.insert(0, line)
        current_tokens += tokens
        
    return "".join(lines)

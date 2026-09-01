import time
import requests
import uuid
from core.config import get_config
from core.logging import setup_logger

logger = setup_logger("memory_repo")

def _get_db_url() -> str:
    config = get_config()
    db_url = config.get("firebase_url", "https://pet-ghost-default-rtdb.asia-southeast1.firebasedatabase.app")
    if not db_url.endswith("/"):
        db_url += "/"
    return db_url

def _get_auth_query() -> str:
    secret = get_config().get("firebase_secret", "")
    return f"?auth={secret}" if secret else ""

def store_long_term_memory(companion_id: str, fact: str) -> None:
    if not companion_id or not fact:
        return
    mem_id = str(uuid.uuid4())
    url = f"{_get_db_url()}companion_memory/{companion_id}/{mem_id}.json{_get_auth_query()}"
    data = {
        "id": mem_id,
        "fact": fact,
        "created_at": time.time()
    }
    try:
        requests.put(url, json=data, timeout=5)
        logger.info(f"Stored new long-term memory for companion {companion_id}: {fact}")
    except Exception as e:
        logger.error(f"Failed to store memory to Firebase: {e}")

def get_companion_memories(companion_id: str) -> list[dict]:
    url = f"{_get_db_url()}companion_memory/{companion_id}.json{_get_auth_query()}"
    memories = []
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200 and resp.json():
            data = resp.json()
            memories = list(data.values())
    except Exception as e:
        logger.error(f"Failed to fetch memories from Firebase: {e}")
        
    # Link active goals into memory context
    try:
        from backend.repositories.factory import get_goal_repository
        repo = get_goal_repository()
        active_goals = [g for g in repo.get_goals(companion_id) if g.get("status") == "active"]
        for g in active_goals:
            memories.append({
                "id": f"goal_{g['id']}",
                "fact": f"Current Active Goal: {g['title']} - {g['description']} (Progress: {g['progress']}%)",
                "created_at": g['created_at']
            })
    except Exception as e:
        logger.error(f"Failed to fetch goals for memory context: {e}")
        
    return memories

def edit_memory(companion_id: str, memory_id: str, new_fact: str) -> None:
    url = f"{_get_db_url()}companion_memory/{companion_id}/{memory_id}.json{_get_auth_query()}"
    try:
        # We need to fetch the existing memory to keep created_at, or just patch fact
        patch_data = {"fact": new_fact}
        requests.patch(url, json=patch_data, timeout=5)
        logger.info(f"Edited memory {memory_id} for companion {companion_id}")
    except Exception as e:
        logger.error(f"Failed to edit memory: {e}")

def delete_memory(companion_id: str, memory_id: str) -> None:
    url = f"{_get_db_url()}companion_memory/{companion_id}/{memory_id}.json{_get_auth_query()}"
    try:
        requests.delete(url, timeout=5)
        logger.info(f"Deleted memory {memory_id} for companion {companion_id}")
    except Exception as e:
        logger.error(f"Failed to delete memory: {e}")

def clear_all_memories(companion_id: str) -> None:
    url = f"{_get_db_url()}companion_memory/{companion_id}.json{_get_auth_query()}"
    try:
        requests.delete(url, timeout=5)
        logger.info(f"Cleared all memories for companion {companion_id}")
    except Exception as e:
        logger.error(f"Failed to clear memories: {e}")

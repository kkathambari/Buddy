from fastapi import APIRouter, HTTPException, Depends
from backend.repositories.factory import get_companion_repository, get_memory_repository
from backend.routers.auth import get_current_user
from backend.services.ownership import user_owns_companion
from typing import Any, Dict, List

router = APIRouter(prefix="/api", tags=["dashboard"])

def require_companion_owner(companion_id: str, current_user: dict) -> None:
    if not user_owns_companion(current_user["uid"], companion_id):
        raise HTTPException(status_code=403, detail="You do not own this companion.")

@router.get("/profile", response_model=Dict[str, Any])
def get_profile(companion_id: str = "default_pet", current_user: dict = Depends(get_current_user)):
    require_companion_owner(companion_id, current_user)
    repo = get_companion_repository()
    soul = repo.get(companion_id) or {}
    stats = soul.get("stats", {})
    return {
        "name": soul.get("name", "Buddy"),
        "species": soul.get("species", "Ghost"),
        "rarity": soul.get("rarity", "common"),
        "energy": soul.get("energy", 100.0),
        "mood": soul.get("mood", "Happy"),
        "bond": stats.get("bond", 0),
        "experience": stats.get("experience", 0)
    }

@router.get("/stats", response_model=Dict[str, Any])
def get_stats(companion_id: str = "default_pet", current_user: dict = Depends(get_current_user)):
    require_companion_owner(companion_id, current_user)
    repo = get_companion_repository()
    soul = repo.get(companion_id) or {}
    return soul.get("stats", {})

@router.get("/activity", response_model=List[Dict[str, Any]])
def get_activity(companion_id: str = "default_pet", current_user: dict = Depends(get_current_user)):
    require_companion_owner(companion_id, current_user)
    # Get actual timeline events instead of fabricated data
    try:
        from timeline.history import load_timeline
        timeline = load_timeline()
        # Optionally filter by companion_id if it exists in the event metadata
        return timeline[-10:] # Return most recent 10 events
    except Exception:
        return []

@router.get("/chat/history", response_model=List[Dict[str, Any]])
def get_chat_history(companion_id: str = "default_pet", current_user: dict = Depends(get_current_user)):
    require_companion_owner(companion_id, current_user)
    mem_repo = get_memory_repository()
    history = mem_repo.get_recent_history(companion_id, limit=50)
    
    formatted_history = []
    for msg in history:
        # Assuming msg format is standard dict with role/content
        role = msg.get("role", "user")
        sender = "pet" if role in ("assistant", "system") else "user"
        formatted_history.append({"sender": sender, "text": msg.get("content", "")})
        
    return formatted_history

@router.get("/memories", response_model=List[Dict[str, Any]])
def get_memories(companion_id: str = "default_pet", current_user: dict = Depends(get_current_user)):
    require_companion_owner(companion_id, current_user)
    try:
        from backend.repositories.memory import get_companion_memories
        memories = get_companion_memories(companion_id)
        return memories
    except Exception:
        return []

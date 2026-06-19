from fastapi import APIRouter, HTTPException
from backend.repositories.factory import get_companion_repository
from typing import Any, Dict

router = APIRouter(prefix="/sync", tags=["sync"])

@router.get("/{companion_id}", response_model=Dict[str, Any])
def get_companion_state(companion_id: str):
    companion_repo = get_companion_repository()
    try:
        soul = companion_repo.get(companion_id)
        if not soul:
            # Return a default empty pet outline if not found in db yet
            return {"name": "Buddy", "energy": 100.0, "rarity": "common", "stats": {}, "is_first_run": True, "alive": True}
        return soul
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch state: {e}")

@router.put("/{companion_id}")
def sync_companion_state(companion_id: str, data: Dict[str, Any]):
    companion_repo = get_companion_repository()
    try:
        success = companion_repo.save(companion_id, data)
        if success:
            return {"status": "success"}
        raise HTTPException(status_code=500, detail="Failed to sync state to storage.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {e}")


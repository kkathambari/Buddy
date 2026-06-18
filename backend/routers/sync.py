from fastapi import APIRouter, HTTPException
from backend.repositories.firebase import FirebaseCompanionRepository
from typing import Any, Dict

router = APIRouter(prefix="/sync", tags=["sync"])
companion_repo = FirebaseCompanionRepository()

@router.get("/{companion_id}", response_model=Dict[str, Any])
def get_companion_state(companion_id: str):
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
    try:
        success = companion_repo.save(companion_id, data)
        if success:
            return {"status": "success"}
        raise HTTPException(status_code=500, detail="Failed to sync state to cloud storage.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {e}")

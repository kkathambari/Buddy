from fastapi import APIRouter, HTTPException, Depends
from backend.repositories.factory import get_companion_repository
from backend.routers.auth import get_current_user
from backend.services.ownership import user_owns_companion
from typing import Any, Dict

router = APIRouter(prefix="/sync", tags=["sync"])


def require_companion_owner(companion_id: str, current_user: dict) -> None:
    if not user_owns_companion(current_user["uid"], companion_id):
        raise HTTPException(status_code=403, detail="You do not own this companion.")

@router.get("/{companion_id}", response_model=Dict[str, Any])
def get_companion_state(companion_id: str, current_user: dict = Depends(get_current_user)):
    require_companion_owner(companion_id, current_user)
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
def sync_companion_state(companion_id: str, data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    require_companion_owner(companion_id, current_user)
    companion_repo = get_companion_repository()
    try:
        success = companion_repo.save(companion_id, data)
        if success:
            return {"status": "success"}
        raise HTTPException(status_code=500, detail="Failed to sync state to storage.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {e}")

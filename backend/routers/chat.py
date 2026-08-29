from fastapi import APIRouter, HTTPException, Depends
from backend.schemas.models import ChatRequest, ChatResponse
from backend.repositories.factory import get_companion_repository
from brain.conversation import process_chat
from backend.routers.auth import get_current_user
from backend.routers.sync import require_companion_owner

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatResponse)
def chat_with_companion(payload: ChatRequest, current_user: dict = Depends(get_current_user)):
    require_companion_owner(payload.companion_id, current_user)
    companion_repo = get_companion_repository()
    try:
        # Fetch latest companion stats and energy from database
        soul = companion_repo.get(payload.companion_id) or {}
        stats = soul.get("stats", {})
        energy = soul.get("energy", 100)
        
        response = process_chat(payload.message, stats, energy)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

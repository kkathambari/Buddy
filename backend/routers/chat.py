from fastapi import APIRouter, HTTPException
from backend.schemas.models import ChatRequest, ChatResponse
from backend.repositories.firebase import FirebaseCompanionRepository
from brain.conversation import process_chat

router = APIRouter(prefix="/chat", tags=["chat"])
companion_repo = FirebaseCompanionRepository()

@router.post("", response_model=ChatResponse)
def chat_with_companion(payload: ChatRequest):
    try:
        # Fetch latest companion stats and energy from database
        soul = companion_repo.get(payload.companion_id) or {}
        stats = soul.get("stats", {})
        energy = soul.get("energy", 100)
        
        response = process_chat(payload.message, stats, energy)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

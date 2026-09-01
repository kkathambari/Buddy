from fastapi import APIRouter, HTTPException, Depends
from backend.schemas.models import ChatRequest, ChatResponse
from pydantic import BaseModel
from backend.repositories.factory import get_companion_repository, get_memory_repository
from brain.conversation import process_chat
from backend.routers.auth import get_current_user
from backend.routers.sync import require_companion_owner

from fastapi import Request
from backend.limiter import limiter

router = APIRouter(prefix="/chat", tags=["chat"])

class ConfirmActionRequest(BaseModel):
    companion_id: str
    token: str
    action_raw: str

@router.post("", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat_with_companion(request: Request, payload: ChatRequest, current_user: dict = Depends(get_current_user)):
    require_companion_owner(payload.companion_id, current_user)
    companion_repo = get_companion_repository()
    try:
        from brain.conversation import process_chat
        
        # Fetch latest companion stats and energy from database
        soul = companion_repo.get(payload.companion_id) or {}
        stats = soul.get("stats", {})
        energy = soul.get("energy", 100)

        response_text, action = process_chat(payload.message, stats, energy, companion_id=payload.companion_id, user_uid=current_user["uid"])
        
        return {"response": response_text, "action": action}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/greeting")
def trigger_first_greeting(payload: ChatRequest, current_user: dict = Depends(get_current_user)):
    require_companion_owner(payload.companion_id, current_user)
    companion_repo = get_companion_repository()
    soul = companion_repo.get(payload.companion_id) or {}
    
    # Idempotent check
    if not soul.get("is_first_run", True):
        return {"status": "already_sent"}
        
    soul["is_first_run"] = False
    companion_repo.save(payload.companion_id, soul)
    
    greeting = f"Hi! I'm {soul.get('name', 'Buddy')}. 🐾 What should we call you?"
    
    mem_repo = get_memory_repository()
    # We create a default thread if this is the first run
    thread_id = mem_repo.create_thread(payload.companion_id, "Main Conversation")
    
    history = mem_repo.get(thread_id) or []
    history.append({"sender": "pet", "message": greeting})
    mem_repo.save(thread_id, history)
    
    return {"response": greeting}

@router.get("/threads")
def get_chat_threads(companion_id: str, current_user: dict = Depends(get_current_user)):
    require_companion_owner(companion_id, current_user)
    mem_repo = get_memory_repository()
    threads = mem_repo.get_threads(companion_id)
    return {"threads": threads}

@router.post("/threads")
def create_chat_thread(payload: ChatRequest, current_user: dict = Depends(get_current_user)):
    require_companion_owner(payload.companion_id, current_user)
    mem_repo = get_memory_repository()
    title = payload.message if payload.message else "New Conversation"
    thread_id = mem_repo.create_thread(payload.companion_id, title)
    return {"thread_id": thread_id, "title": title}

@router.get("/history")
def get_thread_history(companion_id: str, thread_id: str = None, current_user: dict = Depends(get_current_user)):
    require_companion_owner(companion_id, current_user)
    mem_repo = get_memory_repository()
    
    # If thread_id isn't provided, just use companion_id for backwards compatibility or fetch latest
    tid = thread_id if thread_id else companion_id
    
    # Ensure thread_id belongs to this companion
    if tid != companion_id:
        threads = mem_repo.get_threads(companion_id)
        if tid not in [t["id"] for t in threads]:
            raise HTTPException(status_code=403, detail="Thread does not belong to this companion.")

    history = mem_repo.get_recent_history(tid, limit=50)
    return history

@router.post("/confirm_action")
def confirm_action(payload: ConfirmActionRequest, current_user: dict = Depends(get_current_user)):
    require_companion_owner(payload.companion_id, current_user)
    
    import re
    match = re.search(r'\[(OPEN|BROWSE):\s*(.+?)\]', payload.action_raw, flags=re.IGNORECASE)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid action format")
        
    tool_name = match.group(1).lower()
    target = match.group(2).strip()
    params = {"target": target}
    
    from core.automation import execute_action
    result = execute_action(tool_name, params, payload.token)
    
    if not result.get("success"):
        raise HTTPException(status_code=403, detail=result.get("error", "Action execution failed"))
        
    return {"status": "success", "message": result.get("message")}

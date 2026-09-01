from fastapi import APIRouter, Depends, HTTPException, Body
from backend.routers.auth import get_current_user
from backend.repositories.memory import get_companion_memories, store_long_term_memory, edit_memory, delete_memory, clear_all_memories
from backend.services.ownership import user_owns_companion

router = APIRouter(prefix="/api/memory", tags=["memory"])

def verify_ownership(user_uid: str, companion_id: str):
    if not user_owns_companion(user_uid, companion_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this companion's memory")

@router.get("/{companion_id}")
def list_memories(companion_id: str, current_user: dict = Depends(get_current_user)):
    try:
        verify_ownership(current_user["uid"], companion_id)
        memories = get_companion_memories(companion_id)
        return {"memories": memories}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{companion_id}")
def add_memory(companion_id: str, fact: str = Body(..., embed=True), current_user: dict = Depends(get_current_user)):
    try:
        verify_ownership(current_user["uid"], companion_id)
        store_long_term_memory(companion_id, fact)
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{companion_id}/{memory_id}")
def update_memory(companion_id: str, memory_id: str, fact: str = Body(..., embed=True), current_user: dict = Depends(get_current_user)):
    try:
        verify_ownership(current_user["uid"], companion_id)
        edit_memory(companion_id, memory_id, fact)
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{companion_id}/{memory_id}")
def remove_memory(companion_id: str, memory_id: str, current_user: dict = Depends(get_current_user)):
    try:
        verify_ownership(current_user["uid"], companion_id)
        delete_memory(companion_id, memory_id)
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{companion_id}")
def clear_memories(companion_id: str, current_user: dict = Depends(get_current_user)):
    try:
        verify_ownership(current_user["uid"], companion_id)
        clear_all_memories(companion_id)
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

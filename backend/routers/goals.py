import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from backend.repositories.factory import get_goal_repository
from backend.routers.auth import get_current_user
from backend.services.ownership import user_owns_companion
from pydantic import BaseModel

logger = logging.getLogger("goals_router")

router = APIRouter(
    prefix="/api/goals",
    tags=["Goals"],
    dependencies=[Depends(get_current_user)]
)

class GoalCreate(BaseModel):
    companion_id: str
    title: str
    description: Optional[str] = ""

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[float] = None

def verify_access(user: Dict[str, Any], companion_id: str):
    if not user_owns_companion(user["uid"], companion_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this companion's goals")

def sanitize_text(text: str) -> str:
    if not text:
        return text
    return text.replace("[", "").replace("]", "")

@router.get("")
def list_goals(companion_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve all goals for a companion."""
    verify_access(user, companion_id)
    repo = get_goal_repository()
    return {"goals": repo.get_goals(companion_id)}

@router.post("")
def create_goal(goal: GoalCreate, user: Dict[str, Any] = Depends(get_current_user)):
    """Create a new goal."""
    verify_access(user, goal.companion_id)
    repo = get_goal_repository()
    
    goal_data = goal.model_dump() if hasattr(goal, "model_dump") else goal.dict()
    goal_data["title"] = sanitize_text(goal_data.get("title", ""))
    goal_data["description"] = sanitize_text(goal_data.get("description", ""))
    
    goal_id = repo.create_goal(goal_data)
    if not goal_id:
        raise HTTPException(status_code=500, detail="Failed to create goal")
        
    return {"message": "Goal created", "goal_id": goal_id}

@router.put("/{goal_id}")
def update_goal(goal_id: str, companion_id: str, update: GoalUpdate, user: Dict[str, Any] = Depends(get_current_user)):
    """Update a goal's progress or status."""
    verify_access(user, companion_id)
    repo = get_goal_repository()
    
    # Prune None values
    update_data = {k: v for k, v in (update.model_dump() if hasattr(update, "model_dump") else update.dict()).items() if v is not None}
    
    if "title" in update_data:
        update_data["title"] = sanitize_text(update_data["title"])
    if "description" in update_data:
        update_data["description"] = sanitize_text(update_data["description"])
    
    if not repo.update_goal(goal_id, companion_id, update_data):
        raise HTTPException(status_code=404, detail="Goal not found or failed to update")
        
    return {"message": "Goal updated successfully"}

@router.delete("/{goal_id}")
def delete_goal(goal_id: str, companion_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """Delete a goal."""
    verify_access(user, companion_id)
    repo = get_goal_repository()
    if not repo.delete_goal(goal_id, companion_id):
        raise HTTPException(status_code=404, detail="Goal not found")
        
    return {"message": "Goal deleted successfully"}

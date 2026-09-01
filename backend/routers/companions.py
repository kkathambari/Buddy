from fastapi import APIRouter, HTTPException, Depends
from backend.repositories.factory import get_companion_repository
from backend.routers.auth import get_current_user
from backend.services.ownership import get_user_companions, claim_companion
import uuid

router = APIRouter(prefix="/companions", tags=["companions"])

@router.get("")
def list_companions(current_user: dict = Depends(get_current_user)):
    user_uid = current_user["uid"]
    companion_ids = get_user_companions(user_uid)
    
    companion_repo = get_companion_repository()
    companions = []
    
    for c_id in companion_ids:
        soul = companion_repo.get(c_id)
        if soul:
            companions.append({
                "id": c_id,
                "name": soul.get("name", "Buddy"),
                "species": soul.get("species", "Ghost"),
                "stats": soul.get("stats", {})
            })
            
    return {"companions": companions}

from pydantic import BaseModel
class CreateCompanionRequest(BaseModel):
    name: str
    species: str
    stats: dict

@router.post("")
def create_companion(payload: CreateCompanionRequest, current_user: dict = Depends(get_current_user)):
    user_uid = current_user["uid"]
    new_id = str(uuid.uuid4())
    
    companion_repo = get_companion_repository()
    
    initial_soul = {
        "name": payload.name,
        "species": payload.species,
        "energy": 100.0,
        "bond": 0,
        "stats": payload.stats,
        "is_first_run": True,
        "alive": True
    }
    
    companion_repo.save(new_id, initial_soul)
    claim_companion(user_uid, new_id)
    
    return {"id": new_id, "name": payload.name, "species": payload.species, "stats": payload.stats}

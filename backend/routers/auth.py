from fastapi import APIRouter, HTTPException, Depends, Header
from backend.schemas.models import LoginRequest, AuthResponse, LinkRequest
from backend.services.identity import FirebaseIdentityService
from backend.repositories.factory import get_companion_repository
from backend.services.ownership import claim_companion

router = APIRouter(prefix="/auth", tags=["auth"])
identity_service = FirebaseIdentityService()

def get_current_user(authorization: str = Header(None)):
    """Middleware dependency to parse and verify Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    
    token = authorization.split(" ")[1]
    user = identity_service.verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token.")
    return user

@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    auth_data = identity_service.authenticate_user(payload.email, payload.password)
    if not auth_data:
        raise HTTPException(status_code=400, detail="Invalid email or password.")
    return auth_data

@router.post("/link")
def link_seed(payload: LinkRequest, current_user: dict = Depends(get_current_user)):
    user_uid = current_user.get("uid")
    if not claim_companion(user_uid, payload.soul_seed):
        raise HTTPException(status_code=403, detail="This companion is already linked to another user.")
    companion_repo = get_companion_repository()
    # Save the mapping User ID -> Companion Seed in database
    try:
        success = companion_repo.save(f"user_mapping/{user_uid}", {"soul_seed": payload.soul_seed})
        if success:
            return {"status": "success", "message": "Soul Seed linked to user profile successfully."}
        raise HTTPException(status_code=500, detail="Failed to save mapping to repository.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel, EmailStr
from typing import Any, Dict, Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    token: str
    uid: str
    email: str
    refresh_token: Optional[str] = None
    expires_in: Optional[str] = None

class LinkRequest(BaseModel):
    soul_seed: str

class ChatRequest(BaseModel):
    message: str
    companion_id: str = "default_pet"

class ChatResponse(BaseModel):
    response: str

class SoulSyncData(BaseModel):
    name: str = "Buddy"
    energy: float = 100.0
    rarity: str = "common"
    stats: Dict[str, float] = {}
    is_first_run: bool = True
    alive: bool = True

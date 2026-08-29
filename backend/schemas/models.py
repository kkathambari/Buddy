from pydantic import BaseModel, EmailStr, Field
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
    soul_seed: str = Field(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8_000)
    companion_id: str = Field(default="default_pet", min_length=3, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")

class ChatResponse(BaseModel):
    response: str

class SoulSyncData(BaseModel):
    name: str = "Buddy"
    energy: float = 100.0
    rarity: str = "common"
    stats: Dict[str, float] = {}
    is_first_run: bool = True
    alive: bool = True

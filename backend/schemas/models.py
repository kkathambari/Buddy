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
    message: str = Field(min_length=1, max_length=500)
    companion_id: str = Field(default="default_pet", min_length=3, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")

class ChatResponse(BaseModel):
    response: str
    action: Optional[str] = None

class SoulSyncData(BaseModel):
    name: str = "Buddy"
    species: str = "Ghost"
    rarity: str = "common"
    energy: float = 100.0
    mood: str = "Happy"
    bond: int = 45
    experience: int = 12
    stats: Dict[str, float] = {}
    activity: list = []
    is_first_run: bool = True
    alive: bool = True

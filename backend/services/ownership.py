"""Server-side companion ownership checks.

Ownership is deliberately stored separately from mutable companion state so a
client cannot transfer ownership by writing a crafted sync payload.
"""

import time
import requests
from sqlalchemy import Column, String, Float
from backend.db import Base, engine, SessionLocal
from core.logging import setup_logger
from core.auth import hash_seed
from core.config import get_config

logger = setup_logger("ownership")

class CompanionOwner(Base):
    __tablename__ = "companion_owners"
    companion_id = Column(String, primary_key=True)
    user_uid = Column(String, nullable=False)
    created_at = Column(Float, nullable=False, default=time.time)

def init_ownership_store() -> None:
    # Safely creates all tables defined in Base (including companion_owners)
    Base.metadata.create_all(bind=engine)

def _sync_ownership_to_firebase(user_uid: str, companion_id: str) -> None:
    config = get_config()
    db_url = config.get("firebase_url", "https://pet-ghost-default-rtdb.asia-southeast1.firebasedatabase.app")
    if not db_url.endswith("/"):
        db_url += "/"
    secret = config.get("firebase_secret", "")
    auth_query = f"?auth={secret}" if secret else ""
    hashed_id = hash_seed(companion_id)
    url = f"{db_url}user_mapping/{user_uid}/{hashed_id}.json{auth_query}"
    try:
        requests.put(url, json=True, timeout=5)
    except Exception as e:
        logger.error(f"Failed to sync ownership to Firebase: {e}")

def claim_companion(user_uid: str, companion_id: str) -> bool:
    """Claim an unowned companion, or allow its existing owner to relink it."""
    init_ownership_store()
    with SessionLocal() as db:
        owner = db.query(CompanionOwner).filter(CompanionOwner.companion_id == companion_id).first()
        if owner and owner.user_uid != user_uid:
            return False
        if not owner:
            new_owner = CompanionOwner(
                companion_id=companion_id,
                user_uid=user_uid,
                created_at=time.time()
            )
            db.add(new_owner)
            db.commit()
        _sync_ownership_to_firebase(user_uid, companion_id)
        return True

def user_owns_companion(user_uid: str, companion_id: str) -> bool:
    init_ownership_store()
    with SessionLocal() as db:
        owner = db.query(CompanionOwner).filter(
            CompanionOwner.companion_id == companion_id,
            CompanionOwner.user_uid == user_uid
        ).first()
        return owner is not None

def get_user_companions(user_uid: str) -> list[str]:
    init_ownership_store()
    with SessionLocal() as db:
        owners = db.query(CompanionOwner).filter(
            CompanionOwner.user_uid == user_uid
        ).all()
        return [owner.companion_id for owner in owners]

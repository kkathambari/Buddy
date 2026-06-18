import requests
from typing import Any, Dict, Optional
from backend.repositories.base import BaseCompanionRepository, BaseMemoryRepository
from core.config import get_config
from core.exceptions import DatabaseException
from core.logging import setup_logger
from core.auth import hash_seed

logger = setup_logger("firebase_repository")

class FirebaseRepositoryMixin:
    """Provides shared properties for Firebase Realtime Database repositories."""
    @property
    def db_url(self) -> str:
        config = get_config()
        url = config.get("firebase_url", "https://pet-ghost-default-rtdb.asia-southeast1.firebasedatabase.app")
        if not url.endswith("/"):
            url += "/"
        return url

class FirebaseCompanionRepository(BaseCompanionRepository, FirebaseRepositoryMixin):
    """Concrete Firebase Realtime Database implementation for Companion Soul data."""

    def get(self, id: str) -> Optional[Dict[str, Any]]:
        hashed_id = hash_seed(id)
        url = f"{self.db_url}pets/{hashed_id}.json"
        try:
            logger.info(f"Fetching companion soul from Firebase: {hashed_id}")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Firebase returned status {response.status_code} for get {hashed_id}")
                return None
        except Exception as e:
            logger.error(f"Failed to fetch companion from Firebase: {e}", exc_info=True)
            raise DatabaseException(f"Firebase get failed: {e}")

    def save(self, id: str, data: Dict[str, Any]) -> bool:
        hashed_id = hash_seed(id)
        url = f"{self.db_url}pets/{hashed_id}.json"
        try:
            logger.info(f"Saving companion soul to Firebase: {hashed_id}")
            response = requests.put(url, json=data, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to save companion to Firebase: {e}", exc_info=True)
            raise DatabaseException(f"Firebase save failed: {e}")

    def delete(self, id: str) -> bool:
        hashed_id = hash_seed(id)
        url = f"{self.db_url}pets/{hashed_id}.json"
        try:
            logger.info(f"Deleting companion soul from Firebase: {hashed_id}")
            response = requests.delete(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to delete companion from Firebase: {e}", exc_info=True)
            raise DatabaseException(f"Firebase delete failed: {e}")

    def get_stats(self, companion_id: str) -> Optional[Dict[str, Any]]:
        soul = self.get(companion_id)
        if soul:
            return soul.get("stats")
        return None

class FirebaseMemoryRepository(BaseMemoryRepository, FirebaseRepositoryMixin):
    """Concrete Firebase Realtime Database implementation for Chat History."""

    def get(self, id: str) -> Optional[Dict[str, Any]]:
        hashed_id = hash_seed(id)
        url = f"{self.db_url}memories/{hashed_id}.json"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            raise DatabaseException(f"Firebase memory get failed: {e}")

    def save(self, id: str, data: Dict[str, Any]) -> bool:
        hashed_id = hash_seed(id)
        url = f"{self.db_url}memories/{hashed_id}.json"
        try:
            response = requests.put(url, json=data, timeout=5)
            return response.status_code == 200
        except Exception as e:
            raise DatabaseException(f"Firebase memory save failed: {e}")

    def delete(self, id: str) -> bool:
        hashed_id = hash_seed(id)
        url = f"{self.db_url}memories/{hashed_id}.json"
        try:
            response = requests.delete(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            raise DatabaseException(f"Firebase memory delete failed: {e}")

    def get_recent_history(self, session_id: str, limit: int = 20) -> list:
        history = self.get(session_id)
        if isinstance(history, list):
            return history[-limit:]
        return []

import requests
from typing import Any, Dict, Optional
from core.exceptions import AuthException, DatabaseException
from core.logging import setup_logger

logger = setup_logger("forge_sdk")

class ForgeSDK:
    """
    Forge SDK Client.
    Used by Desktop, Android, and Web clients to authenticate, sync stats,
    and trigger cognitive capabilities over the network.
    """
    def __init__(self, backend_url: str = None):
        self.backend_url = backend_url or "http://localhost:8000"
        self.user_token: Optional[str] = None
        self.user_uid: Optional[str] = None
        self.user_email: Optional[str] = None
        self.soul_seed: Optional[str] = None

    def login(self, email: str, password: str) -> bool:
        """Authenticates user email/password with the backend identity service."""
        try:
            logger.info(f"Authenticating user '{email}' via SDK.")
            
            # Send login request to FastAPI backend
            response = requests.post(
                f"{self.backend_url}/auth/login",
                json={"email": email, "password": password},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get("token")
                self.user_uid = data.get("uid")
                self.user_email = data.get("email")
                logger.info(f"User login successful. UID: {self.user_uid}")
                return True
            else:
                logger.warning(f"Login failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Network error during SDK login: {e}")
            # Fallback direct call if backend is not yet deployed (helps in development)
            try:
                from backend.services.identity import FirebaseIdentityService
                service = FirebaseIdentityService()
                auth_data = service.authenticate_user(email, password)
                if auth_data:
                    self.user_token = auth_data.get("token")
                    self.user_uid = auth_data.get("uid")
                    self.user_email = auth_data.get("email")
                    return True
            except Exception as fe:
                logger.error(f"Fallback direct login also failed: {fe}")
            return False

    def link_companion(self, soul_seed: str) -> bool:
        """Links the logged-in user profile to a unique 3-word Soul Seed."""
        if not self.user_uid:
            raise AuthException("User must be authenticated to link a companion.")
            
        try:
            logger.info(f"Linking user profile '{self.user_uid}' to seed '{soul_seed}'.")
            headers = {"Authorization": f"Bearer {self.user_token}"}
            response = requests.post(
                f"{self.backend_url}/auth/link",
                json={"soul_seed": soul_seed},
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                self.soul_seed = soul_seed
                return True
            return False
        except Exception as e:
            logger.error(f"Network error during companion link: {e}")
            # Local fallback registry save
            try:
                from backend.repositories.factory import get_companion_repository
                repo = get_companion_repository()
                # Store user mapping
                repo.save(f"user_mapping/{self.user_uid}", {"soul_seed": soul_seed})
                self.soul_seed = soul_seed
                return True
            except Exception as fe:
                logger.error(f"Fallback direct link failed: {fe}")
            return False

    def sync_companion_state(self, soul_data: Dict[str, Any]) -> bool:
        """Synchronizes companion stats, mood, and energy to the cloud repository."""
        companion_id = self.soul_seed or "default_pet"
        try:
            headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
            response = requests.put(
                f"{self.backend_url}/sync/{companion_id}",
                json=soul_data,
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"SDK failed to sync stats over network: {e}")
            # Fallback direct cloud sync
            try:
                from backend.repositories.factory import get_companion_repository
                repo = get_companion_repository()
                return repo.save(companion_id, soul_data)
            except Exception as fe:
                logger.error(f"Fallback companion sync failed: {fe}")
            return False

    def get_companion_state(self) -> Optional[Dict[str, Any]]:
        """Downloads the latest synchronized companion state."""
        companion_id = self.soul_seed or "default_pet"
        try:
            headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
            response = requests.get(
                f"{self.backend_url}/sync/{companion_id}",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"SDK failed to fetch companion state over network: {e}")
            try:
                from backend.repositories.factory import get_companion_repository
                repo = get_companion_repository()
                return repo.get(companion_id)
            except Exception as fe:
                logger.error(f"Fallback companion fetch failed: {fe}")
            return None

    def send_chat_message(self, message: str) -> str:
        """Sends a message to the conversational engine and receives response."""
        companion_id = self.soul_seed or "default_pet"
        try:
            headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
            response = requests.post(
                f"{self.backend_url}/chat",
                json={"message": message, "companion_id": companion_id},
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("response", "")
            return "Hmm... I couldn't reach the server."
        except Exception as e:
            logger.error(f"SDK failed to send chat message over network: {e}")
            try:
                from brain.conversation import process_chat
                from backend.repositories.factory import get_companion_repository
                repo = get_companion_repository()
                soul = repo.get(companion_id) or {"energy": 100}
                stats = soul.get("stats", {})
                energy = soul.get("energy", 100)
                return process_chat(message, stats, energy)
            except Exception as fe:
                logger.error(f"Fallback direct chat failed: {fe}")
            return "I'm here... just a little disconnected."

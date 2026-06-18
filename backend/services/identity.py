from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import requests
from core.config import get_config
from core.exceptions import AuthException
from core.logging import setup_logger

logger = setup_logger("identity_service")

class BaseIdentityService(ABC):
    """Abstract Identity and Authentication Service interface."""
    
    @abstractmethod
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifies a user authentication token.
        Returns user details dict (e.g. uid, email) if valid, or None if invalid.
        """
        pass

    @abstractmethod
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticates a user via email and password credentials.
        Returns a dict containing token and user profile on success, or None on failure.
        """
        pass

class FirebaseIdentityService(BaseIdentityService):
    """Concrete Identity Service implementing Firebase Authentication REST API client."""

    @property
    def api_key(self) -> str:
        config = get_config()
        # Fallback to a default key if none configured for demo/setup purposes
        return config.get("firebase_api_key", "")

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifies Firebase ID token using Google Identity Toolkit REST API.
        Endpoint: https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=[API_KEY]
        """
        if not self.api_key:
            logger.warning("Firebase API key missing. Returning mock verification for token.")
            return {"uid": "mock_user_123", "email": "dev@forge.ai"}

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={self.api_key}"
        try:
            response = requests.post(url, json={"idToken": token}, timeout=5)
            if response.status_code == 200:
                users = response.json().get("users", [])
                if users:
                    user_data = users[0]
                    return {
                        "uid": user_data.get("localId"),
                        "email": user_data.get("email"),
                        "email_verified": user_data.get("emailVerified", False)
                    }
            else:
                logger.warning(f"Token lookup failed with status: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error calling Firebase token lookup: {e}", exc_info=True)
            raise AuthException(f"Token verification failed: {e}")

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Signs in a user with email and password via Firebase Auth REST API.
        Endpoint: https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=[API_KEY]
        """
        if not self.api_key:
            logger.warning("Firebase API key missing. Mocking success sign-in.")
            return {
                "token": "mock_jwt_token_abc123",
                "uid": "mock_user_123",
                "email": email
            }

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
        try:
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                res_data = response.json()
                return {
                    "token": res_data.get("idToken"),
                    "uid": res_data.get("localId"),
                    "email": res_data.get("email"),
                    "refresh_token": res_data.get("refreshToken"),
                    "expires_in": res_data.get("expiresIn")
                }
            else:
                logger.warning(f"Authentication failed with status: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error calling Firebase signIn: {e}", exc_info=True)
            raise AuthException(f"User authentication failed: {e}")

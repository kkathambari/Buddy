from core.logging import setup_logger

logger = setup_logger("base_connector")

class BaseConnector:
    """
    Base API Connector.
    Establishes security scope checks and mocks fallback behaviors if credentials are missing.
    """
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.credentials_cache = {}

    def has_credentials(self) -> bool:
        """Checks if service credentials are configured locally."""
        return len(self.credentials_cache) > 0

    def set_credentials(self, credentials: dict) -> None:
        """Sets credentials configuration."""
        self.credentials_cache = credentials
        logger.info(f"Loaded credentials for connector service: '{self.service_name}'")

    def validate_scope(self, required_scope: str) -> bool:
        """Verifies if the loaded credentials contain the required scopes."""
        if not self.has_credentials():
            return False
        allowed_scopes = self.credentials_cache.get("scopes", [])
        return required_scope in allowed_scopes

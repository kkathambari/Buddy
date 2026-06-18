class ForgeAIException(Exception):
    """Base exception class for all Forge AI errors."""
    def __init__(self, message: str = "An unexpected error occurred in Forge AI.", details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class ConfigException(ForgeAIException):
    """Exception raised for errors in loading or updating configuration settings."""
    pass

class AuthException(ForgeAIException):
    """Exception raised for identity verification or token authentication failures."""
    pass

class DatabaseException(ForgeAIException):
    """Exception raised for operations failing at the repository or cloud sync layers."""
    pass

class BrainException(ForgeAIException):
    """Exception raised for cognitive reasoning, routing, or intent processing failures."""
    pass

class CapabilityException(ForgeAIException):
    """Exception raised when execution of an optional capability (e.g. Education, Career) fails."""
    pass

class GatewayException(ForgeAIException):
    """Exception raised for LLM model inference connection timeouts or invalid responses."""
    pass

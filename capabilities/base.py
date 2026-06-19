from abc import ABC, abstractmethod
from typing import Any, Dict

class Capability(ABC):
    """
    Abstract Base Class for all pluggable Forge AI capabilities.
    Defines strict contracts for lifecycle execution, context checking, and sandbox logging.
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """Runs once on startup/loading to verify directories and settings."""
        pass

    @abstractmethod
    def observe(self, context: Dict[str, Any]) -> None:
        """Receives ambient contextual updates (foreground activities)."""
        pass

    @abstractmethod
    def execute(self, intent: Dict[str, Any], stats: Dict[str, Any], energy: float) -> str:
        """Processes intent payload, handles active session dialogs, and returns response."""
        pass

    @abstractmethod
    def reflect(self) -> Dict[str, Any]:
        """Provides feedback logs and computes trust/bond metric increases."""
        pass

    @abstractmethod
    def update_memory(self) -> None:
        """Persists local session statistics inside the capability's sandbox directory."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Safely saves session state and releases resources on system exit."""
        pass

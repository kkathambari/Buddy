from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseRepository(ABC):
    """Abstract base repository defining standard lifecycle operations."""
    
    @abstractmethod
    def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an object by its identifier."""
        pass

    @abstractmethod
    def save(self, id: str, data: Dict[str, Any]) -> bool:
        """Saves or updates an object with the given identifier."""
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Deletes an object by its identifier."""
        pass

class BaseCompanionRepository(BaseRepository, ABC):
    """Repository interface specifically for Companion soul data sync."""
    
    @abstractmethod
    def get_stats(self, companion_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves stats dict for a given companion identifier."""
        pass

class BaseMemoryRepository(BaseRepository, ABC):
    """Repository interface specifically for storing and retrieving past chat logs."""
    
    @abstractmethod
    def get_recent_history(self, session_id: str, limit: int = 20) -> list:
        """Retrieves the last N records from a chat log."""
        pass

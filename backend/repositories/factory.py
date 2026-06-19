from core.config import get_config
from backend.repositories.sqlite import SqliteCompanionRepository, SqliteMemoryRepository
from backend.repositories.firebase import FirebaseCompanionRepository, FirebaseMemoryRepository

def get_companion_repository():
    """Returns the configured companion repository implementation."""
    config = get_config()
    if config.get("repository_type", "sqlite") == "firebase":
        return FirebaseCompanionRepository()
    return SqliteCompanionRepository()

def get_memory_repository():
    """Returns the configured memory repository implementation."""
    config = get_config()
    if config.get("repository_type", "sqlite") == "firebase":
        return FirebaseMemoryRepository()
    return SqliteMemoryRepository()

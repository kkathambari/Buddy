from core.config import get_config
from backend.repositories.sqlite import SqliteCompanionRepository, SqliteMemoryRepository, SqliteGoalRepository
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

def get_goal_repository():
    """Returns the configured goal repository implementation."""
    # Only sqlite for now
    return SqliteGoalRepository()

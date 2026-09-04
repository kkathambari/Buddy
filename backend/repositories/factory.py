from core.config import get_config
from backend.repositories.sqlite import SqliteCompanionRepository, SqliteMemoryRepository, SqliteGoalRepository, SqlitePlannerRepository, SqliteScheduleRepository
from backend.repositories.postgres import PostgresCompanionRepository, PostgresMemoryRepository, PostgresGoalRepository, PostgresPlannerRepository, PostgresScheduleRepository
from backend.repositories.firebase import FirebaseCompanionRepository, FirebaseMemoryRepository

def get_companion_repository():
    """Returns the configured companion repository implementation."""
    config = get_config()
    if config.get("repository_type", "sqlite") == "firebase":
        return FirebaseCompanionRepository()
    if config.get("repository_type", "sqlite") == "postgres":
        return PostgresCompanionRepository()
    return SqliteCompanionRepository()

def get_memory_repository():
    """Returns the configured memory repository implementation."""
    config = get_config()
    if config.get("repository_type", "sqlite") == "firebase":
        return FirebaseMemoryRepository()
    if config.get("repository_type", "sqlite") == "postgres":
        return PostgresMemoryRepository()
    return SqliteMemoryRepository()

def get_goal_repository():
    """Returns the configured goal repository implementation."""
    config = get_config()
    if config.get("repository_type", "sqlite") == "postgres":
        return PostgresGoalRepository()
    return SqliteGoalRepository()

def get_planner_repository():
    """Returns the configured planner repository implementation."""
    config = get_config()
    if config.get("repository_type", "sqlite") == "postgres":
        return PostgresPlannerRepository()
    return SqlitePlannerRepository()

def get_schedule_repository():
    """Returns the configured schedule repository implementation."""
    config = get_config()
    if config.get("repository_type", "sqlite") == "postgres":
        return PostgresScheduleRepository()
    return SqliteScheduleRepository()

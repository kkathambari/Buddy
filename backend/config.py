from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings, enforced via pydantic-settings.
    Validates that required environment variables are present on startup.
    """
    app_env: str = "production"
    
    openai_api_key: Optional[str] = None
    firebase_credentials: Optional[str] = None
    database_url: str = "sqlite:///data/buddy.db"
    
    # Model defaults
    buddy_openai_model: str = "gpt-4o-mini"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

def get_settings() -> Settings:
    settings = Settings()
    if settings.app_env in ["development", "test"]:
        if not settings.openai_api_key:
            settings.openai_api_key = "mock_key"
        if not settings.firebase_credentials:
            settings.firebase_credentials = "{}"
    else:
        if not settings.openai_api_key or not settings.firebase_credentials:
            raise ValueError("OPENAI_API_KEY and FIREBASE_CREDENTIALS must be set in production")
    return settings

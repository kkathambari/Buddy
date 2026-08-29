"""Fail-fast production configuration validation."""
import os


def validate_production_configuration() -> None:
    if os.getenv("BUDDY_ENV", "development").lower() != "production":
        return
    required = ("OPENAI_API_KEY", "FIREBASE_API_KEY", "BUDDY_CORS_ORIGINS")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError("Missing required production configuration: " + ", ".join(missing))
    if os.getenv("BUDDY_ENABLE_TERMINAL_TOOL", "").lower() == "true":
        raise RuntimeError("Terminal tool must remain disabled in production.")

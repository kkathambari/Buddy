import os
from typing import Dict
from shared.storage import safe_load, safe_save

FLAGS_FILE = "data/feature_flags.json"

class FeatureFlags:
    """
    Manages runtime and persistent feature flags for DevBuddy capabilities.
    """
    
    _default_flags = {
        "education": True,
        "career": True,
        "voice": True,
        "proactive": True,
        "attention_engine": True,
        "experience_engine": True,
        "analytics": True
    }
    
    _cached_flags: Dict[str, bool] = {}
    
    @classmethod
    def _load_flags(cls) -> Dict[str, bool]:
        """Loads flags from the JSON storage, falling back to default states."""
        if not cls._cached_flags:
            loaded = safe_load(FLAGS_FILE, {})
            # Merge loaded with defaults
            cls._cached_flags = {**cls._default_flags, **loaded}
        return cls._cached_flags
        
    @classmethod
    def is_enabled(cls, name: str) -> bool:
        """Checks if a feature flag is enabled."""
        flags = cls._load_flags()
        return flags.get(name, False)
        
    @classmethod
    def set_flag(cls, name: str, value: bool) -> None:
        """Sets a feature flag and persists the updated configuration."""
        flags = cls._load_flags()
        flags[name] = value
        cls._cached_flags = flags
        os.makedirs(os.path.dirname(FLAGS_FILE), exist_ok=True)
        safe_save(FLAGS_FILE, flags)
        
    @classmethod
    def reset_defaults(cls) -> None:
        """Resets flags to default states."""
        cls._cached_flags = cls._default_flags.copy()
        if os.path.exists(FLAGS_FILE):
            try:
                os.remove(FLAGS_FILE)
            except Exception:
                pass

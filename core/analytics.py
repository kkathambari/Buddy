import os
import time
from typing import Dict, Any, List
from shared.storage import safe_load, safe_save
from core.feature_flags import FeatureFlags

ANALYTICS_FILE = "data/product_analytics.json"

class ProductAnalytics:
    """
    Manages recording and reading product analytics events locally.
    """
    
    @classmethod
    def track_event(cls, event_name: str, metadata: Dict[str, Any] = None) -> None:
        """Logs a product usage event with a timestamp if the analytics feature flag is active."""
        if not FeatureFlags.is_enabled("analytics"):
            return
            
        try:
            events = safe_load(ANALYTICS_FILE, [])
            if not isinstance(events, list):
                events = []
                
            event_entry = {
                "event": event_name,
                "timestamp": time.time(),
                "metadata": metadata or {}
            }
            events.append(event_entry)
            os.makedirs(os.path.dirname(ANALYTICS_FILE), exist_ok=True)
            safe_save(ANALYTICS_FILE, events)
        except Exception:
            pass # Prevent crashes due to analytics logging failures
            
    @classmethod
    def get_events(cls) -> List[Dict[str, Any]]:
        """Retrieves all logged events."""
        return safe_load(ANALYTICS_FILE, [])
        
    @classmethod
    def clear_events(cls) -> None:
        """Clears all logged events."""
        if os.path.exists(ANALYTICS_FILE):
            try:
                os.remove(ANALYTICS_FILE)
            except Exception:
                pass

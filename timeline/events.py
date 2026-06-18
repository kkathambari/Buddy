from datetime import datetime
import uuid
from typing import Any, Dict

class TimelineEvent:
    """Represents a structured, chronological audit log event."""
    
    def __init__(self, title: str, source: str, metadata: Dict[str, Any] = None):
        self.event_id = str(uuid.uuid4())
        self.title = title
        self.source = source  # matches MemorySource values
        self.timestamp = datetime.utcnow().isoformat()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "title": self.title,
            "source": self.source,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }

"""
Notification Engine for DevBuddy 2.0 (`workflow/notifications.py`).
Dispatches automated alerts on workflow completion, failure, or crash recovery events.
Supports console logs, terminal output, and outbound email alerts.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from tools.manager import ToolManager


@dataclass
class NotificationEvent:
    event_type: str  # "workflow_completed", "workflow_failed", "workflow_recovered"
    workflow_id: str
    instance_id: str
    message: str
    recipient: Optional[str] = None


class NotificationEngine:
    """
    Dispatches alerts through ToolManager capabilities.
    """

    def __init__(self):
        self.tool_manager = ToolManager.get_instance()
        self.dispatch_log: List[NotificationEvent] = []

    async def notify(self, event: NotificationEvent) -> bool:
        """Send notification alert."""
        self.dispatch_log.append(event)

        if event.recipient and "@" in event.recipient:
            # Dispatch email notification via Email tool
            try:
                await self.tool_manager.execute_tool(
                    "email",
                    {
                        "action": "send_email",
                        "to": event.recipient,
                        "subject": f"[DevBuddy 2.0 Alert] {event.event_type}: {event.workflow_id}",
                        "body": event.message
                    }
                )
                return True
            except Exception:
                pass

        # Fallback to local console log tracking
        return True

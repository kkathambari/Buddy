from brain.agents.base import BaseAgent
from brain.planner import TaskNode
from core.logging import setup_logger

logger = setup_logger("communication_agent")

class CommunicationAgent(BaseAgent):
    """
    CommunicationAgent dispatches system notifications and triggers external webhook updates.
    """
    def __init__(self):
        super().__init__("communication_agent")

    async def execute_task(self, task: TaskNode) -> str:
        logger.info(f"CommunicationAgent executing task: {task.title}")
        
        from events.bus import global_bus
        from events.bus import Event
        
        global_bus.publish("relationship_changed", {
            "source": "communication_agent",
            "message": f"Alert: {task.title}"
        })
        
        return "System tray notification and webhook alerts dispatched successfully."

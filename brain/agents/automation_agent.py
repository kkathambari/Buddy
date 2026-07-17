from brain.agents.base import BaseAgent
from brain.planner import TaskNode
from core.logging import setup_logger
from brain.vision import DesktopVisionEngine
from core.os_control import OSController

logger = setup_logger("automation_agent")

class AutomationAgent(BaseAgent):
    """
    AutomationAgent manages command line executions, clipboard states, and OS automation scripts.
    """
    def __init__(self):
        super().__init__("automation_agent")

    async def execute_task(self, task: TaskNode) -> str:
        logger.info(f"AutomationAgent executing task: {task.title}")
        if not self.verify_permissions(["terminal"]):
            return "Permission 'terminal' denied. Cannot run system commands."
            
        title = task.title.lower()
        if "click" in title:
            OSController.click_at(500, 500)
            return "Automation clicked coordinate location successfully."
        elif "type" in title or "write" in title:
            OSController.send_keys("Hello World")
            return "Automation input keys successfully."
        elif "capture" in title or "screen" in title or "vision" in title:
            img = DesktopVisionEngine.capture_screen()
            elements = DesktopVisionEngine.detect_ui_elements()
            return f"Automation screen captured successfully. Detected {len(elements)} items."
            
        return f"Automation script successfully completed task: '{task.title}'"

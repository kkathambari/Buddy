import os
from brain.agents.base import BaseAgent
from brain.planner import TaskNode
from core.logging import setup_logger

logger = setup_logger("research_agent")

class ResearchAgent(BaseAgent):
    """
    ResearchAgent scans workspace files, searches for keywords, and summarizes docs.
    """
    def __init__(self):
        super().__init__("research_agent")

    async def execute_task(self, task: TaskNode) -> str:
        logger.info(f"ResearchAgent executing task: {task.title}")
        if not self.verify_permissions(["filesystem"]):
            return "Permission 'filesystem' denied. Cannot perform research."
            
        workspace = "e:\\claude-code-main"
        docs_found = []
        try:
            for root, dirs, files in os.walk(workspace):
                if len(docs_found) > 10:
                    break
                for file in files:
                    if file.endswith((".md", ".txt")):
                        docs_found.append(os.path.join(root, file))
        except Exception as e:
            logger.error(f"Error scanning files in research: {e}")
            
        summary = f"Scanned workspace. Found {len(docs_found)} documentation/text files.\n"
        if docs_found:
            summary += f"Primary sources: {', '.join([os.path.basename(f) for f in docs_found[:3]])}"
        return summary

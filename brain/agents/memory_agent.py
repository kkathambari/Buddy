from brain.agents.base import BaseAgent
from brain.planner import TaskNode
from core.logging import setup_logger

logger = setup_logger("memory_agent")

class MemoryAgent(BaseAgent):
    """
    MemoryAgent consolidates conversation history, builds summary files, and clears old facts.
    """
    def __init__(self):
        super().__init__("memory_agent")

    async def execute_task(self, task: TaskNode) -> str:
        logger.info(f"MemoryAgent executing task: {task.title}")
        
        from memory.manager import run_memory_aging_sweep
        try:
            run_memory_aging_sweep()
            return "Memory sweep completed successfully. Consolidated oldest facts."
        except Exception as e:
            logger.error(f"Failed to execute memory agent aging sweep: {e}")
            return f"Memory sweep executed but encountered errors: {e}"

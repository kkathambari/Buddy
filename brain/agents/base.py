from abc import ABC, abstractmethod
from typing import List
from core.permissions import global_permission_manager
from brain.planner import TaskNode
from core.logging import setup_logger

logger = setup_logger("base_agent")

class BaseAgent(ABC):
    """
    Abstract Base Class for all specialized sub-agents.
    Coordinates lifecycle and enforces local security permissions.
    """
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    @abstractmethod
    async def execute_task(self, task: TaskNode) -> str:
        """Executes a parsed task node asynchronously. Returns execution details."""
        pass

    def verify_permissions(self, required_perms: List[str]) -> bool:
        """Checks permissions with the Global Permission Manager before tool usage."""
        return global_permission_manager.verify_skill_permissions(self.agent_id, required_perms)

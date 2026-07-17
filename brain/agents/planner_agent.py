from brain.agents.base import BaseAgent
from brain.planner import TaskNode, global_planner
from core.logging import setup_logger

logger = setup_logger("planner_agent")

class PlannerAgent(BaseAgent):
    """
    PlannerAgent coordinates goal decomposition graphs and delegates active subtasks.
    """
    def __init__(self):
        super().__init__("planner_agent")

    async def execute_task(self, task: TaskNode) -> str:
        logger.info(f"PlannerAgent executing task: {task.title}")
        goal = task.title
        plan = global_planner.create_plan("planner_agent_run", goal)
        return f"Generated task dependency graph with {len(plan.tasks)} stages."

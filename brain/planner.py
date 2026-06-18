from typing import Any, Dict, List
from core.logging import setup_logger

logger = setup_logger("planner")

class TaskPlan:
    """Represents a planned series of actions to accomplish a user goal."""
    def __init__(self, goal: str, steps: List[str]):
        self.goal = goal
        self.steps = steps
        self.current_step_index = 0
        self.completed = False

    def next_step(self) -> Optional[str]:
        if self.current_step_index < len(self.steps):
            step = self.steps[self.current_step_index]
            self.current_step_index += 1
            if self.current_step_index >= len(self.steps):
                self.completed = True
            return step
        return None

class CognitivePlanner:
    """Creates step-by-step plans for complex user requests (e.g. studying, job application)."""
    
    def __init__(self):
        self.active_plans: Dict[str, TaskPlan] = {}

    def create_plan(self, companion_id: str, goal: str, steps: List[str]) -> TaskPlan:
        logger.info(f"Creating plan for {companion_id}: '{goal}' with {len(steps)} steps.")
        plan = TaskPlan(goal, steps)
        self.active_plans[companion_id] = plan
        return plan

    def get_plan(self, companion_id: str) -> Optional[TaskPlan]:
        return self.active_plans.get(companion_id)

    def clear_plan(self, companion_id: str) -> None:
        if companion_id in self.active_plans:
            del self.active_plans[companion_id]
            logger.info(f"Cleared plan for companion {companion_id}")

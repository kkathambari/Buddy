import json
import re
from typing import Any, Dict, List, Optional, Set
from core.logging import setup_logger
from ai.gateway.broker import AIGateway

logger = setup_logger("planner")

class TaskNode:
    """Represents a single node/step in the execution dependency graph."""
    def __init__(self, task_id: str, title: str, agent: str, dependencies: List[str] = None, verification: str = "", description: str = ""):
        self.task_id = task_id
        self.title = title
        self.agent = agent # target agent/handler, e.g. 'education', 'coding', 'automation'
        self.dependencies = dependencies or []
        self.status = "pending" # pending, running, completed, failed
        self.result = None
        self.verification = verification
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "agent": self.agent,
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result,
            "verification": self.verification,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskNode':
        node = cls(
            task_id=data["task_id"],
            title=data["title"],
            agent=data["agent"],
            dependencies=data.get("dependencies", []),
            verification=data.get("verification", ""),
            description=data.get("description", "")
        )
        node.status = data.get("status", "pending")
        node.result = data.get("result", None)
        return node


class TaskPlan:
    """Represents a planned execution dependency graph to accomplish a user goal."""
    def __init__(self, goal: str, tasks: List[TaskNode]):
        self.goal = goal
        self.tasks: Dict[str, TaskNode] = {t.task_id: t for t in tasks}
        self.completed = False

    def get_executable_tasks(self) -> List[TaskNode]:
        """Returns a list of tasks that are pending and whose dependencies are completed."""
        executable = []
        for task in self.tasks.values():
            if task.status == "pending":
                # Check dependencies
                deps_met = True
                for dep_id in task.dependencies:
                    dep = self.tasks.get(dep_id)
                    if not dep or dep.status != "completed":
                        deps_met = False
                        break
                if deps_met:
                    executable.append(task)
        return executable

    def mark_task_status(self, task_id: str, status: str, result: Any = None) -> None:
        """Updates the status and result of a specific task node."""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            if result is not None:
                self.tasks[task_id].result = result
            logger.info(f"Task '{task_id}' marked as '{status}'.")
            
            # Check if all tasks are completed
            all_done = all(t.status == "completed" for t in self.tasks.values())
            if all_done:
                self.completed = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "tasks": [t.to_dict() for t in self.tasks.values()],
            "completed": self.completed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskPlan':
        tasks = [TaskNode.from_dict(t) for t in data.get("tasks", [])]
        plan = cls(goal=data["goal"], tasks=tasks)
        plan.completed = data.get("completed", False)
        return plan


class CognitivePlanner:
    """Creates structured, dependency-based execution plans dynamically using LLMs or fallbacks."""
    
    def __init__(self):
        self.active_plans: Dict[str, TaskPlan] = {}

    def create_plan(self, companion_id: str, goal: str) -> TaskPlan:
        """Decomposes a goal into a TaskPlan graph, using LLM analysis or a structured rules fallback."""
        logger.info(f"Decomposing goal for '{companion_id}': '{goal}'")
        
        prompt = f"""
You are an execution planner. Decompose the user's goal into a structured dependency graph of tasks.
Target Agents: 'education' (for learning/quizzes), 'coding' (for writing/analyzing code), 'career' (for resume/interviews), 'automation' (for shell/file scripts).

Goal: "{goal}"

Response Format: Return ONLY a valid JSON array of objects with no markdown blocks. Each object represents a task:
{{
  "task_id": "unique_id_string (e.g. task_0, task_1)",
  "title": "Clear description of the step",
  "agent": "education|coding|career|automation",
  "dependencies": ["list_of_dependency_ids"],
  "verification": "what condition defines success"
}}

Example response:
[
  {{"task_id": "task_0", "title": "Review FastAPI fundamentals", "agent": "education", "dependencies": [], "verification": "Quiz passed"}},
  {{"task_id": "task_1", "title": "Create FastAPI basic skeleton", "agent": "coding", "dependencies": ["task_0"], "verification": "Code compiles"}}
]
"""
        tasks = []
        try:
            response = AIGateway.generate_response(prompt).strip()
            # Parse JSON block
            if response.startswith("```"):
                lines = response.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].strip() == "```":
                    lines = lines[:-1]
                response = "\n".join(lines).strip()
            
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                tasks_data = json.loads(json_match.group(0))
                for t in tasks_data:
                    tasks.append(TaskNode(
                        task_id=t["task_id"],
                        title=t["title"],
                        agent=t["agent"],
                        dependencies=t.get("dependencies", []),
                        verification=t.get("verification", "")
                    ))
        except Exception as e:
            logger.warning(f"LLM Planner failed or offline: {e}. Utilizing rules-based fallback.")
            
        # Fallback to rules-based template if LLM fails or returns empty list
        if not tasks:
            tasks = self._get_fallback_tasks(goal)

        plan = TaskPlan(goal, tasks)
        self.active_plans[companion_id] = plan
        return plan

    def _get_fallback_tasks(self, goal: str) -> List[TaskNode]:
        """Provides hardcoded fallback dependency graphs based on keyword mappings."""
        goal_lower = goal.lower()
        if "study" in goal_lower or "learn" in goal_lower or "quiz" in goal_lower or "viva" in goal_lower:
            return [
                TaskNode("task_0", f"Review concepts relating to '{goal}'", "education", [], "Review completed"),
                TaskNode("task_1", "Take Mock Viva check", "education", ["task_0"], "Quiz passed")
            ]
        elif "code" in goal_lower or "write" in goal_lower or "build" in goal_lower or "project" in goal_lower:
            return [
                TaskNode("task_0", "Decompose architecture specifications", "coding", [], "Architecture designed"),
                TaskNode("task_1", "Write code files and structures", "coding", ["task_0"], "Files written"),
                TaskNode("task_2", "Verify functionality with test scripts", "coding", ["task_1"], "Tests passed")
            ]
        elif "career" in goal_lower or "resume" in goal_lower or "interview" in goal_lower:
            return [
                TaskNode("task_0", "Extract ATS profile match guidelines", "career", [], "Guidelines extracted"),
                TaskNode("task_1", "Run mock coaching practice", "career", ["task_0"], "Practice complete")
            ]
        else:
            # Default generic 2-step plan
            return [
                TaskNode("task_0", f"Analyze request for '{goal}'", "automation", [], "Analysis done"),
                TaskNode("task_1", "Execute general request", "automation", ["task_0"], "Execution complete")
            ]

    def get_plan(self, companion_id: str) -> Optional[TaskPlan]:
        return self.active_plans.get(companion_id)

    def clear_plan(self, companion_id: str) -> None:
        if companion_id in self.active_plans:
            del self.active_plans[companion_id]
            logger.info(f"Cleared plan for companion {companion_id}")

# Global singleton planner
global_planner = CognitivePlanner()

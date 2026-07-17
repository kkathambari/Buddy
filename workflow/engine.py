"""
Workflow Engine for DevBuddy 2.0 (`workflow/engine.py`).
Central governance and state machine for workflow definitions and instances.
Handles step progression, pause/resume/cancel controls, and crash recovery.
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from .storage import WorkflowStorage, WorkflowDefinition, WorkflowInstance, WorkflowStep
from .executor import WorkflowExecutor


class WorkflowEngine:
    """
    Singleton state machine coordinating workflow execution loops.
    """

    _instance: Optional["WorkflowEngine"] = None

    def __init__(self, db_path: str = "data/workflows.db"):
        self.storage = WorkflowStorage(db_path=db_path)
        self.executor = WorkflowExecutor()

    @classmethod
    def get_instance(cls, db_path: str = "data/workflows.db") -> "WorkflowEngine":
        if cls._instance is None:
            cls._instance = cls(db_path=db_path)
        return cls._instance

    def register_definition(self, definition: WorkflowDefinition):
        """Save definition into SQLite database."""
        self.storage.save_definition(definition)

    def get_definition(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self.storage.get_definition(workflow_id)

    def start_workflow(self, workflow_id: str, initial_context: Optional[Dict[str, Any]] = None) -> WorkflowInstance:
        """Create and persist a new running workflow instance."""
        defn = self.storage.get_definition(workflow_id)
        if not defn or not defn.is_active:
            raise ValueError(f"Active workflow definition '{workflow_id}' not found.")

        first_step_id = defn.steps[0].step_id if defn.steps else None
        inst = WorkflowInstance(
            instance_id=f"inst_{int(time.time() * 1000)}_{workflow_id[:6]}",
            workflow_id=workflow_id,
            status="RUNNING" if first_step_id else "COMPLETED",
            current_step_id=first_step_id,
            context_data=initial_context or {}
        )
        self.storage.save_instance(inst)
        return inst

    async def run_instance_until_blocked(self, instance_id: str) -> WorkflowInstance:
        """
        Continuously execute steps for the given instance until completion, failure, or pause.
        """
        inst = self.storage.get_instance(instance_id)
        if not inst or inst.status not in ["RUNNING", "PENDING"]:
            return inst or WorkflowInstance(instance_id, "", "FAILED", None)

        inst.status = "RUNNING"
        defn = self.storage.get_definition(inst.workflow_id)
        if not defn:
            inst.status = "FAILED"
            inst.error_summary = "Workflow definition missing during execution."
            self.storage.save_instance(inst)
            return inst

        steps_map = {s.step_id: s for s in defn.steps}

        while inst.current_step_id and inst.status == "RUNNING":
            step = steps_map.get(inst.current_step_id)
            if not step:
                inst.status = "FAILED"
                inst.error_summary = f"Step '{inst.current_step_id}' not found in definition."
                break

            next_id, step_status = await self.executor.execute_step(step, inst)

            if step_status == "error" and next_id is None:
                inst.status = "FAILED"
                inst.current_step_id = None
                break
            else:
                inst.current_step_id = next_id
                if next_id is None and step_status == "success":
                    inst.status = "COMPLETED"

            self.storage.save_instance(inst)

        if not inst.current_step_id and inst.status == "RUNNING":
            inst.status = "COMPLETED"
            self.storage.save_instance(inst)

        return inst

    def pause_workflow(self, instance_id: str) -> bool:
        """Transition running instance to PAUSED status."""
        inst = self.storage.get_instance(instance_id)
        if inst and inst.status == "RUNNING":
            inst.status = "PAUSED"
            self.storage.save_instance(inst)
            return True
        return False

    async def resume_workflow(self, instance_id: str) -> Optional[WorkflowInstance]:
        """Resume a PAUSED workflow instance."""
        inst = self.storage.get_instance(instance_id)
        if inst and inst.status == "PAUSED":
            inst.status = "RUNNING"
            self.storage.save_instance(inst)
            return await self.run_instance_until_blocked(instance_id)
        return inst

    def cancel_workflow(self, instance_id: str) -> bool:
        """Permanently terminate a workflow instance."""
        inst = self.storage.get_instance(instance_id)
        if inst and inst.status in ["RUNNING", "PAUSED", "PENDING"]:
            inst.status = "CANCELLED"
            self.storage.save_instance(inst)
            return True
        return False

    async def recover_crashed_instances(self) -> List[WorkflowInstance]:
        """Find instances that were interrupted in RUNNING state during crash/shutdown and resume them."""
        recoverable = self.storage.get_recoverable_instances()
        recovered = []
        for inst in recoverable:
            res = await self.run_instance_until_blocked(inst.instance_id)
            recovered.append(res)
        return recovered

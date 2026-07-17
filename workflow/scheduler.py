"""
Workflow Scheduler for DevBuddy 2.0 (`workflow/scheduler.py`).
Asynchronously polls active triggers, launches new execution instances, and manages retry backoff.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from .triggers import TriggerEngine, BaseTrigger
from .engine import WorkflowEngine
from .storage import WorkflowInstance


class WorkflowScheduler:
    """
    Background scheduler loop checking triggers and dispatching async executions.
    """

    def __init__(self, engine: Optional[WorkflowEngine] = None):
        self.engine = engine or WorkflowEngine.get_instance()
        self.trigger_engine = TriggerEngine()
        self._is_running = False
        self._poll_interval_seconds = 1.0

    def register_trigger(self, trigger: BaseTrigger):
        self.trigger_engine.register_trigger(trigger)

    async def step_cycle(self, system_context: Dict[str, Any]) -> List[WorkflowInstance]:
        """Perform a single check cycle over all triggers and run dispatched instances."""
        events = self.trigger_engine.evaluate_all(system_context)
        launched = []
        for ev in events:
            try:
                inst = self.engine.start_workflow(ev.workflow_id, initial_context=ev.payload)
                # Run asynchronously without blocking the scheduler loop
                asyncio.create_task(self.engine.run_instance_until_blocked(inst.instance_id))
                launched.append(inst)
            except Exception:
                pass
        return launched

    async def start_loop(self, get_context_fn: Any):
        """Start background execution loop."""
        self._is_running = True
        while self._is_running:
            ctx = get_context_fn() if callable(get_context_fn) else {}
            await self.step_cycle(ctx)
            await asyncio.sleep(self._poll_interval_seconds)

    def stop_loop(self):
        self._is_running = False

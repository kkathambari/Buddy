"""
Trigger Engine for DevBuddy 2.0 (`workflow/triggers.py`).
Orchestrates event detection across 4 trigger types:
1. TimeTrigger: Cron schedule or recurring interval (`interval_seconds`, `cron_expr`)
2. EventTrigger: External system events (`file_change`, `git_commit`, `system_alert`)
3. ConditionTrigger: Threshold checks (`resource_usage > threshold`)
4. ManualTrigger: Explicit API or user command execution
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from .conditions import ConditionEvaluator


@dataclass
class TriggerEvent:
    trigger_type: str
    workflow_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class BaseTrigger(ABC):
    def __init__(self, workflow_id: str, trigger_id: str):
        self.workflow_id = workflow_id
        self.trigger_id = trigger_id
        self.is_active = True

    @abstractmethod
    def check(self, system_context: Dict[str, Any]) -> Optional[TriggerEvent]:
        pass


class TimeTrigger(BaseTrigger):
    """Trigger based on recurring interval in seconds."""
    def __init__(self, workflow_id: str, trigger_id: str, interval_seconds: float):
        super().__init__(workflow_id, trigger_id)
        self.interval_seconds = interval_seconds
        self.last_triggered = 0.0

    def check(self, system_context: Dict[str, Any]) -> Optional[TriggerEvent]:
        now = time.time()
        if now - self.last_triggered >= self.interval_seconds:
            self.last_triggered = now
            return TriggerEvent(
                trigger_type="time",
                workflow_id=self.workflow_id,
                payload={"interval_seconds": self.interval_seconds, "time": now}
            )
        return None


class EventTrigger(BaseTrigger):
    """Trigger based on event bus notification matching `event_name`."""
    def __init__(self, workflow_id: str, trigger_id: str, event_name: str):
        super().__init__(workflow_id, trigger_id)
        self.event_name = event_name

    def check(self, system_context: Dict[str, Any]) -> Optional[TriggerEvent]:
        events: List[Dict[str, Any]] = system_context.get("recent_events", [])
        for ev in events:
            if ev.get("event_name") == self.event_name:
                return TriggerEvent(
                    trigger_type="event",
                    workflow_id=self.workflow_id,
                    payload=ev.get("payload", {})
                )
        return None


class ConditionTrigger(BaseTrigger):
    """Trigger based on composite condition rule tree over `system_context`."""
    def __init__(self, workflow_id: str, trigger_id: str, condition_rule: Dict[str, Any]):
        super().__init__(workflow_id, trigger_id)
        self.condition_rule = condition_rule
        self._was_met = False

    def check(self, system_context: Dict[str, Any]) -> Optional[TriggerEvent]:
        is_met = ConditionEvaluator.evaluate(self.condition_rule, system_context)
        # Edge trigger: fire only when condition transitions from False to True
        if is_met and not self._was_met:
            self._was_met = True
            return TriggerEvent(
                trigger_type="condition",
                workflow_id=self.workflow_id,
                payload={"context_snapshot": system_context}
            )
        elif not is_met:
            self._was_met = False
        return None


class TriggerEngine:
    """
    Registers and evaluates active triggers against global system context.
    """

    def __init__(self):
        self.triggers: Dict[str, BaseTrigger] = {}

    def register_trigger(self, trigger: BaseTrigger):
        self.triggers[trigger.trigger_id] = trigger

    def unregister_trigger(self, trigger_id: str):
        self.triggers.pop(trigger_id, None)

    def evaluate_all(self, system_context: Dict[str, Any]) -> List[TriggerEvent]:
        """Poll active triggers and return fired events."""
        fired = []
        for t in self.triggers.values():
            if not t.is_active:
                continue
            ev = t.check(system_context)
            if ev:
                fired.append(ev)
        return fired

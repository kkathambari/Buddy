"""
Unit and Integration Test Suite for DevBuddy 2.0 Workflow Engine (`workflow/`).
Verifies:
- WorkflowStorage: SQLite definition and instance persistence
- ConditionEvaluator: Composite AND/OR/NOT and numerical comparison rules
- TriggerEngine: TimeTrigger, EventTrigger, ConditionTrigger evaluations
- WorkflowExecutor & Engine: Multi-step transition (`assign -> condition -> tool/llm -> complete/fail`)
- WorkflowBuilder: Natural language specification to `WorkflowDefinition`
- Crash Recovery: Resuming instances interrupted in `RUNNING` state
- WorkflowHistory & NotificationEngine: Audit query filtering and event alerting
"""

import unittest
import asyncio
import os
import shutil
import time
from typing import Dict, Any

from workflow.storage import WorkflowStorage, WorkflowDefinition, WorkflowInstance, WorkflowStep
from workflow.conditions import ConditionEvaluator
from workflow.triggers import TriggerEngine, TimeTrigger, EventTrigger, ConditionTrigger
from workflow.executor import WorkflowExecutor
from workflow.engine import WorkflowEngine
from workflow.builder import WorkflowBuilder
from workflow.scheduler import WorkflowScheduler
from workflow.history import WorkflowHistory
from workflow.notifications import NotificationEngine, NotificationEvent
from tools.registry import ToolRegistry
from tools.filesystem.tool import FilesystemTool


class TestWorkflowEngine(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db_dir = "tests/temp_workflow_data"
        os.makedirs(cls.test_db_dir, exist_ok=True)
        cls.db_path = f"{cls.test_db_dir}/test_workflows.db"

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db_dir):
            shutil.rmtree(cls.test_db_dir, ignore_errors=True)

    async def asyncSetUp(self):
        # Reset storage cleanly
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.engine = WorkflowEngine.get_instance(db_path=self.db_path)
        self.engine.storage = WorkflowStorage(db_path=self.db_path)
        ToolRegistry.get_instance().discover_and_register_defaults()

    def test_storage_and_conditions(self):
        """Verify SQLite persistence and composite condition evaluator."""
        storage = WorkflowStorage(db_path=self.db_path)
        step1 = WorkflowStep("s1", "Assign X", "assign", {"key": "x", "value": 10}, next_step_id="s2")
        defn = WorkflowDefinition("wf_test_1", "Test Workflow", "Desc", [step1])
        storage.save_definition(defn)

        loaded = storage.get_definition("wf_test_1")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.steps[0].action_type, "assign")

        # Test composite conditions
        ctx = {"status": "ok", "metrics": {"cpu": 85, "memory": 40}}
        rule = {
            "operator": "AND",
            "rules": [
                {"field": "status", "op": "==", "value": "ok"},
                {"field": "metrics.cpu", "op": ">", "value": 80}
            ]
        }
        self.assertTrue(ConditionEvaluator.evaluate(rule, ctx))
        self.assertFalse(ConditionEvaluator.evaluate({"field": "metrics.memory", "op": ">", "value": 50}, ctx))

    def test_trigger_engine(self):
        """Verify TimeTrigger, EventTrigger, and ConditionTrigger firing mechanics."""
        t_engine = TriggerEngine()
        time_trig = TimeTrigger("wf_1", "t_1", interval_seconds=0.1)
        ev_trig = EventTrigger("wf_2", "e_1", event_name="git_push")
        cond_trig = ConditionTrigger("wf_3", "c_1", {"field": "alert", "op": "==", "value": True})

        t_engine.register_trigger(time_trig)
        t_engine.register_trigger(ev_trig)
        t_engine.register_trigger(cond_trig)

        # Check evaluate_all
        sys_ctx = {"recent_events": [{"event_name": "git_push", "payload": {"branch": "main"}}], "alert": True}
        events = t_engine.evaluate_all(sys_ctx)
        self.assertGreaterEqual(len(events), 2)
        wf_ids = [e.workflow_id for e in events]
        self.assertIn("wf_2", wf_ids)
        self.assertIn("wf_3", wf_ids)

    async def test_multi_step_execution_and_branching(self):
        """Verify end-to-end execution of a multi-step workflow with assignment, conditional branching, and tool calls."""
        steps = [
            WorkflowStep("s1", "Init Counter", "assign", {"key": "count", "value": 5}, next_step_id="s2"),
            WorkflowStep("s2", "Check Count", "condition", {"rule": {"field": "count", "op": ">", "value": 3}, "true_step_id": "s3_true", "false_step_id": "s3_false"}),
            WorkflowStep("s3_true", "List Dir Tool", "tool", {"tool_name": "filesystem", "arguments": {"operation": "list", "path": "."}}, next_step_id=None),
            WorkflowStep("s3_false", "Should Not Run", "assign", {"key": "failed_branch", "value": True}, next_step_id=None)
        ]
        defn = WorkflowDefinition("wf_branch_test", "Branching Test", "Tests conditional execution", steps)
        self.engine.register_definition(defn)

        inst = self.engine.start_workflow("wf_branch_test", {"initial": "data"})
        completed_inst = await self.engine.run_instance_until_blocked(inst.instance_id)

        self.assertEqual(completed_inst.status, "COMPLETED")
        self.assertEqual(completed_inst.context_data["count"], 5)
        self.assertIn("s3_true", completed_inst.context_data)
        self.assertNotIn("failed_branch", completed_inst.context_data)

    async def test_natural_language_builder(self):
        """Verify natural language conversion into WorkflowDefinition using builder templates."""
        nl_prompt = "Every morning at 9 AM check open PRs and summarize via LLM"
        defn = await WorkflowBuilder.build_from_nl(nl_prompt, workflow_id="wf_nl_1")
        self.assertEqual(defn.workflow_id, "wf_nl_1")
        self.assertGreaterEqual(len(defn.steps), 2)
        self.assertEqual(defn.steps[0].action_type, "tool")
        self.assertEqual(defn.steps[1].action_type, "llm")

    async def test_crash_recovery_and_history(self):
        """Verify recovery of crashed instances left in RUNNING state and audit queries."""
        steps = [
            WorkflowStep("s1", "Assign First", "assign", {"key": "step1_done", "value": True}, next_step_id="s2"),
            WorkflowStep("s2", "Final Assign", "assign", {"key": "recovered_done", "value": True}, next_step_id=None)
        ]
        defn = WorkflowDefinition("wf_crash", "Crash Test", "Testing recovery", steps)
        self.engine.register_definition(defn)

        # Simulate crash: save instance manually with status='RUNNING' and current_step_id='s2'
        crashed_inst = WorkflowInstance("inst_crashed_1", "wf_crash", "RUNNING", "s2", {"step1_done": True})
        self.engine.storage.save_instance(crashed_inst)

        # Perform recovery
        recovered_list = await self.engine.recover_crashed_instances()
        self.assertEqual(len(recovered_list), 1)
        self.assertEqual(recovered_list[0].status, "COMPLETED")
        self.assertTrue(recovered_list[0].context_data.get("recovered_done"))

        # Verify history query
        history = WorkflowHistory(db_path=self.db_path)
        runs = history.query(workflow_id="wf_crash", status="COMPLETED")
        self.assertEqual(len(runs), 1)

    async def test_notifications(self):
        """Verify NotificationEngine dispatch logs events without errors."""
        notifier = NotificationEngine()
        ev = NotificationEvent("workflow_completed", "wf_crash", "inst_crashed_1", "Finished successfully", "dev@devbuddy.ai")
        success = await notifier.notify(ev)
        self.assertTrue(success)
        self.assertEqual(len(notifier.dispatch_log), 1)


if __name__ == "__main__":
    unittest.main()

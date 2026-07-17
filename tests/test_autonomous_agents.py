import os
import sys
import unittest
import asyncio
import time
from unittest.mock import MagicMock, patch

# Add root folder to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from brain.agents.base import BaseAgent
from brain.agents.planner_agent import PlannerAgent
from brain.agents.research_agent import ResearchAgent
from brain.agents.coding_agent import CodingAgent
from brain.agents.document_agent import DocumentAgent
from brain.agents.automation_agent import AutomationAgent
from brain.agents.memory_agent import MemoryAgent
from brain.agents.communication_agent import CommunicationAgent

from brain.planner import TaskNode, TaskPlan, global_planner
from brain.reasoner import CognitiveReasoner
from core.permissions import global_permission_manager
from core.runtime import global_runtime

class TestAutonomousAgents(unittest.TestCase):
    
    def setUp(self):
        # Whitelist permissions for tests
        global_permission_manager.set_local_only_mode(True)
        global_permission_manager.grant_permission("coding_agent", "filesystem")
        global_permission_manager.grant_permission("coding_agent", "terminal")
        global_permission_manager.grant_permission("research_agent", "filesystem")
        global_permission_manager.grant_permission("document_agent", "filesystem")
        global_permission_manager.grant_permission("automation_agent", "terminal")
        
        # Reset planner plans
        global_planner.active_plans.clear()

    def tearDown(self):
        # Reset planner plans
        global_planner.active_plans.clear()
        
    async def run_async_test_task(self, agent, node):
        return await agent.execute_task(node)

    def test_base_agent_permission_checks(self):
        agent = CodingAgent()
        self.assertTrue(agent.verify_permissions(["filesystem", "terminal"]))
        self.assertFalse(agent.verify_permissions(["system_control"]))

    def test_planner_agent(self):
        agent = PlannerAgent()
        node = TaskNode("task_0", "study FastAPI concepts", "planner")
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(self.run_async_test_task(agent, node))
            self.assertIn("Generated task dependency graph", res)
        finally:
            loop.close()

    def test_research_agent(self):
        agent = ResearchAgent()
        node = TaskNode("task_0", "find python doc files", "career")
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(self.run_async_test_task(agent, node))
            self.assertIn("Scanned workspace", res)
        finally:
            loop.close()

    def test_coding_agent(self):
        agent = CodingAgent()
        node = TaskNode("task_0", "run unit tests", "coding")
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(self.run_async_test_task(agent, node))
            self.assertTrue("Coding task executed" in res)
        finally:
            loop.close()

    def test_document_agent(self):
        agent = DocumentAgent()
        node = TaskNode("task_0", "parse FastAPI PDF", "education")
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(self.run_async_test_task(agent, node))
            self.assertIn("Document parsed successfully", res)
        finally:
            loop.close()

    def test_automation_agent(self):
        agent = AutomationAgent()
        node = TaskNode("task_0", "launch chrome", "automation")
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(self.run_async_test_task(agent, node))
            self.assertIn("Automation script successfully completed", res)
        finally:
            loop.close()

    def test_memory_agent(self):
        agent = MemoryAgent()
        node = TaskNode("task_0", "consolidate facts", "memory")
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(self.run_async_test_task(agent, node))
            self.assertIn("Memory sweep completed", res)
        finally:
            loop.close()

    def test_communication_agent(self):
        agent = CommunicationAgent()
        node = TaskNode("task_0", "send slack alert", "communication")
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(self.run_async_test_task(agent, node))
            self.assertIn("System tray notification", res)
        finally:
            loop.close()

    @patch('ai.gateway.broker.AIGateway.generate_response')
    def test_reasoner_agent_delegation(self, mock_generate):
        mock_generate.return_value = "Mocked Reasoner Response"
        
        # Register a plan
        plan = global_planner.create_plan("test_reasoner_comp", "study FastAPI concepts")
        
        # First task should be task_0 (agent: education, status: pending)
        self.assertEqual(plan.tasks["task_0"].status, "pending")
        
        # Invoke Reasoner to trigger task_0
        intent = {
            "raw_text": "Let's study now.",
            "companion_id": "test_reasoner_comp",
            "tone": {"emotion": "neutral", "intensity": "low"},
            "emotion": "neutral"
        }
        CognitiveReasoner.reason(intent, {}, 100)
        
        # Wait up to 3.0 seconds for background execution on runtime loop thread to complete
        for _ in range(30):
            if plan.tasks["task_0"].status in ["completed", "failed"]:
                break
            time.sleep(0.1)
            
        self.assertEqual(plan.tasks["task_0"].status, "completed")
        self.assertTrue("Document parsed successfully" in plan.tasks["task_0"].result)

if __name__ == "__main__":
    unittest.main()

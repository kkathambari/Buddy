import os
import sys
import unittest
import shutil
import json
from unittest.mock import MagicMock, patch

# Add root folder to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from brain.planner import TaskNode, TaskPlan, global_planner
from memory.knowledge_graph import KnowledgeGraphManager
from brain.attention import AttentionEngine
from brain.reasoner import CognitiveReasoner
from memory.projects import log_project_decision, get_project_decisions

class TestCognitiveArchitecture(unittest.TestCase):
    
    def setUp(self):
        # Override paths for testing isolation
        self.kg_db = "data/test_knowledge_graph.db"
        self.decisions_file = "data/project_decisions.json"
        
        # Cleanup past test files
        for f in [self.kg_db, self.decisions_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass
                    
        self.kg = KnowledgeGraphManager(self.kg_db)

    def tearDown(self):
        # Close connection and cleanup files
        if hasattr(self, 'kg'):
            del self.kg
            
        for f in [self.kg_db, self.decisions_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass
                    
        # Reset global planner plans
        global_planner.active_plans.clear()

    def test_planner_dependency_graph(self):
        # Create plan using fallback template
        plan = global_planner.create_plan("test_comp", "study FastAPI concepts")
        
        self.assertEqual(plan.goal, "study FastAPI concepts")
        self.assertEqual(len(plan.tasks), 2)
        
        # Verify dependencies
        task_0 = plan.tasks["task_0"]
        task_1 = plan.tasks["task_1"]
        self.assertEqual(task_0.status, "pending")
        self.assertEqual(task_1.status, "pending")
        self.assertEqual(task_1.dependencies, ["task_0"])
        
        # First executable task should be task_0
        exec_tasks = plan.get_executable_tasks()
        self.assertEqual(len(exec_tasks), 1)
        self.assertEqual(exec_tasks[0].task_id, "task_0")
        
        # Mark task_0 running and then completed
        plan.mark_task_status("task_0", "running")
        self.assertEqual(len(plan.get_executable_tasks()), 0)
        
        plan.mark_task_status("task_0", "completed")
        # Now task_1 should be executable
        exec_tasks_new = plan.get_executable_tasks()
        self.assertEqual(len(exec_tasks_new), 1)
        self.assertEqual(exec_tasks_new[0].task_id, "task_1")
        
        # Complete task_1
        plan.mark_task_status("task_1", "completed")
        self.assertTrue(plan.completed)

    def test_knowledge_graph_sqlite(self):
        self.kg.add_node("user_1", "User", "Kathambari")
        self.kg.add_node("proj_1", "Project", "DevBuddy", {"path": "/workspace"})
        self.kg.add_edge("user_1", "proj_1", "owns")
        
        # Retrieve related
        related = self.kg.get_related_nodes("user_1")
        self.assertEqual(len(related), 1)
        self.assertEqual(related[0]["id"], "proj_1")
        self.assertEqual(related[0]["relation"], "owns")
        self.assertEqual(related[0]["properties"]["path"], "/workspace")
        
        # Filter relation
        related_filter = self.kg.get_related_nodes("user_1", "collaborates")
        self.assertEqual(len(related_filter), 0)
        
        # Delete node
        self.kg.delete_node("proj_1")
        self.assertEqual(len(self.kg.get_related_nodes("user_1")), 0)

    def test_attention_token_budget_optimization(self):
        chunks = [
            "This is a small chunk of text.",
            "This represents a significantly larger chunk of text containing more words to simulate token threshold budget cuts."
        ]
        # Restrict budget to fit only the first chunk
        optimized = AttentionEngine.optimize_token_budget(chunks, max_tokens=15)
        self.assertEqual(len(optimized), 1)
        self.assertEqual(optimized[0], chunks[0])
        
        # Truncation check
        optimized_truncate = AttentionEngine.optimize_token_budget(chunks, max_tokens=5)
        self.assertEqual(len(optimized_truncate), 1)
        self.assertTrue(optimized_truncate[0].endswith("..."))

    @patch('core.runtime.AgentRuntime.run_agent_task')
    @patch('ai.gateway.broker.AIGateway.generate_response')
    def test_reasoner_verification_reflection_loop(self, mock_generate, mock_run_agent_task):
        mock_generate.return_value = "Mock Reasoner Output"
        
        # Register a plan
        plan = global_planner.create_plan("test_comp", "build coding project")
        # Start task_0
        plan.mark_task_status("task_0", "running")
        
        # Invoke reasoner with verification keywords (e.g. "done")
        intent = {
            "raw_text": "I am done with the architecture",
            "companion_id": "test_comp",
            "tone": {"emotion": "happy", "intensity": "low"},
            "emotion": "neutral"
        }
        res = CognitiveReasoner.reason(intent, {}, 100)
        
        # Verify that task_0 was marked completed and task_1 was automatically started (status: running)
        self.assertEqual(plan.tasks["task_0"].status, "completed")
        self.assertEqual(plan.tasks["task_1"].status, "running")
        self.assertEqual(res, "Mock Reasoner Output")
        
        # Verify retry strategy (failed keyword)
        intent_fail = {
            "raw_text": "I got an error on the files write",
            "companion_id": "test_comp",
            "tone": {"emotion": "sad", "intensity": "low"},
            "emotion": "neutral"
        }
        CognitiveReasoner.reason(intent_fail, {}, 100)
        # task_1 (which was running) should be reset back to pending due to failure detection
        self.assertEqual(plan.tasks["task_1"].status, "pending")

    def test_project_decisions_caching(self):
        log_project_decision("/workspace", "dec_1", "Database Choice", "accepted", "We used SQLite.")
        decisions = get_project_decisions("/workspace")
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["id"], "dec_1")
        self.assertEqual(decisions[0]["status"], "accepted")

if __name__ == "__main__":
    unittest.main()

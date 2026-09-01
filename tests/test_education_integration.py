import os
import sys
import unittest
import shutil
from unittest.mock import MagicMock, patch

# Add workspace root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from capabilities.education.handler import EducationCapability
from proactive.trigger import proactive_queue
from proactive.cooldowns import reset_cooldown
from relationship.manager import update_relationship

class TestEducationIntegration(unittest.TestCase):

    def setUp(self):
        # Backup user's progress file if it exists
        if os.path.exists("data/learning_progress.json"):
            try:
                os.rename("data/learning_progress.json", "data/learning_progress.json.bak")
            except Exception:
                pass

        # Clear sandbox folder and data
        if os.path.exists("data/sandbox/education"):
            try:
                shutil.rmtree("data/sandbox/education")
            except Exception:
                pass
                
        if os.path.exists("data/relationship.json"):
            try:
                os.remove("data/relationship.json")
            except Exception:
                pass
                
        # Clear proactive queue
        while not proactive_queue['test_companion'].empty():
            try:
                proactive_queue['test_companion'].get_nowait()
            except Exception:
                pass
                
        # Reset cooldowns
        reset_cooldown("education_proactive_quiz")

    def tearDown(self):
        if os.path.exists("data/sandbox/education"):
            try:
                shutil.rmtree("data/sandbox/education")
            except Exception:
                pass
        if os.path.exists("data/relationship.json"):
            try:
                os.remove("data/relationship.json")
            except Exception:
                pass
        # Clean up any progress file created during tests
        if os.path.exists("data/learning_progress.json"):
            try:
                os.remove("data/learning_progress.json")
            except Exception:
                pass
        # Restore user's backup if it exists
        if os.path.exists("data/learning_progress.json.bak"):
            try:
                os.rename("data/learning_progress.json.bak", "data/learning_progress.json")
            except Exception:
                pass

    def test_sandbox_initialization(self):
        cap = EducationCapability()
        self.assertFalse(os.path.exists("data/sandbox/education"))
        cap.initialize()
        self.assertTrue(os.path.exists("data/sandbox/education"))

    @patch('ai.gateway.broker.AIGateway.generate_response')
    def test_execute_sandbox_storage(self, mock_generate):
        mock_generate.return_value = "Mock response"
        
        cap = EducationCapability()
        cap.initialize()
        
        # Start study session
        intent_start = {
            "raw_text": "start session python",
            "companion_id": "test_edu_comp"
        }
        res_start = cap.execute(intent_start, {}, 100)
        self.assertIn("Let's study Python", res_start)
        
        # Execute Viva question answer (this should write progress to sandbox)
        intent_ans = {
            "raw_text": "interpreted language",
            "companion_id": "test_edu_comp"
        }
        cap.execute(intent_ans, {}, 100)
        
        # Assert that the progress is written specifically in the sandbox path
        self.assertTrue(os.path.exists(cap.sandbox_path))
        self.assertFalse(os.path.exists("data/learning_progress.json"), "Progress written outside the sandbox!")
        
        from shared.storage import safe_load
        progress = safe_load(cap.sandbox_path, {})
        self.assertIn("Python", progress)
        self.assertEqual(progress["Python"], 10)

    @patch('ai.gateway.broker.AIGateway.generate_response')
    def test_observe_trust_gates(self, mock_generate):
        mock_generate.return_value = "Viva suggestion comment"
        
        cap = EducationCapability()
        cap.initialize()
        
        # Scenario 1: Low trust (default 0.5)
        update_relationship("test_edu_comp", -0.2, 0, "Set trust low") # trust becomes 0.3
        
        context = {"category": "coding", "companion_id": "test_edu_comp"}
        cap.observe(context)
        
        # Queue should be empty since trust <= 0.7
        self.assertTrue(proactive_queue['test_edu_comp'].empty())
        
        # Scenario 2: High trust (> 0.7)
        update_relationship("test_edu_comp", 0.5, 0, "Set trust high") # trust becomes 0.8
        
        cap.observe(context)
        
        # Queue should contain the proactive study suggestion
        self.assertFalse(proactive_queue['test_edu_comp'].empty())
        msg = proactive_queue['test_edu_comp'].get_nowait()
        self.assertEqual(msg, "Viva suggestion comment")

    def test_lifecycle_hooks(self):
        cap = EducationCapability()
        cap.initialize()
        cap.update_memory()
        cap.shutdown()

if __name__ == "__main__":
    unittest.main()

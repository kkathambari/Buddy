import os
import sys
import unittest
import shutil
from unittest.mock import MagicMock, patch

# Add workspace root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from capabilities.career.handler import CareerCapability
from proactive.trigger import proactive_queue
from proactive.cooldowns import reset_cooldown
from relationship.manager import update_relationship

class TestCareerIntegration(unittest.TestCase):

    def setUp(self):
        # Clear sandbox folder and data
        if os.path.exists("data/sandbox/career"):
            try:
                shutil.rmtree("data/sandbox/career")
            except Exception:
                pass
                
        if os.path.exists("data/relationship.json"):
            try:
                os.remove("data/relationship.json")
            except Exception:
                pass
                
        # Clear proactive queue
        while not proactive_queue.empty():
            try:
                proactive_queue.get_nowait()
            except Exception:
                pass
                
        # Reset cooldowns
        reset_cooldown("career_proactive_ats")

    def tearDown(self):
        if os.path.exists("data/sandbox/career"):
            try:
                shutil.rmtree("data/sandbox/career")
            except Exception:
                pass
        if os.path.exists("data/relationship.json"):
            try:
                os.remove("data/relationship.json")
            except Exception:
                pass

    def test_sandbox_initialization(self):
        cap = CareerCapability()
        self.assertFalse(os.path.exists("data/sandbox/career"))
        cap.initialize()
        self.assertTrue(os.path.exists("data/sandbox/career"))

    @patch('ai.gateway.broker.AIGateway.generate_response')
    def test_execute_sandbox_storage(self, mock_generate):
        mock_generate.return_value = "Mock response"
        
        cap = CareerCapability()
        cap.initialize()
        
        # Start career discussion
        intent_start = {
            "raw_text": "start job prep",
            "companion_id": "test_car_comp"
        }
        res_start = cap.execute(intent_start, {}, 100)
        self.assertIn("What kind of role or internship are we targeting", res_start)
        
        # profiling step (this should write target_role to sandbox profile)
        intent_prof = {
            "raw_text": "backend",
            "companion_id": "test_car_comp"
        }
        cap.execute(intent_prof, {}, 100)
        
        # Assert that the progress is written specifically in the sandbox path
        self.assertTrue(os.path.exists(cap.sandbox_path))
        
        from shared.storage import safe_load
        profile = safe_load(cap.sandbox_path, {})
        self.assertEqual(profile["target_role"], "Backend Developer")

    @patch('ai.gateway.broker.AIGateway.generate_response')
    def test_observe_trust_gates(self, mock_generate):
        mock_generate.return_value = "Mock ATS scan suggestion"
        
        cap = CareerCapability()
        cap.initialize()
        
        # Scenario 1: Low trust (default 0.5)
        update_relationship("test_car_comp", -0.2, 0, "Set trust low") # trust becomes 0.3
        
        context = {"title": "My LinkedIn Jobs", "companion_id": "test_car_comp"}
        cap.observe(context)
        
        # Queue should be empty since trust <= 0.7
        self.assertTrue(proactive_queue.empty())
        
        # Scenario 2: High trust (> 0.7)
        update_relationship("test_car_comp", 0.5, 0, "Set trust high") # trust becomes 0.8
        
        cap.observe(context)
        
        # Queue should contain the proactive career suggestion
        self.assertFalse(proactive_queue.empty())
        msg = proactive_queue.get_nowait()
        self.assertEqual(msg, "Mock ATS scan suggestion")

    def test_lifecycle_hooks(self):
        cap = CareerCapability()
        cap.initialize()
        cap.update_memory()
        cap.shutdown()

if __name__ == "__main__":
    unittest.main()

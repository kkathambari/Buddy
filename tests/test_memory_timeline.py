import os
import sys
import unittest
import json
from unittest.mock import MagicMock, patch

# Add workspace root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from memory.working_memory import load_working_memory, save_working_memory, add_dialog_turn, get_recent_context
from timeline.history import load_timeline, log_timeline_event
from timeline.milestones import load_unlocked_milestones
from memory.manager import evaluate_and_commit

class TestMemoryTimeline(unittest.TestCase):
    
    def setUp(self):
        # Clear temporary test files
        save_working_memory([])
        
        # Reset timeline
        if os.path.exists("data/timeline.json"):
            try:
                os.remove("data/timeline.json")
            except Exception:
                pass

    def test_working_memory_limits(self):
        # Add 25 turns
        for i in range(25):
            add_dialog_turn(f"User query {i}", f"Bot response {i}", "neutral")
            
        memory = load_working_memory()
        # Should be capped at 20 turns
        self.assertEqual(len(memory), 20)
        # Should contain the latest turns
        self.assertEqual(memory[0]["user"], "User query 5")
        self.assertEqual(memory[-1]["user"], "User query 24")
        
        context = get_recent_context(max_tokens=3000)
        self.assertTrue(isinstance(context, str))
        self.assertIn("User: User query 22", context)
        self.assertIn("Buddy: Bot response 24", context)

    def test_timeline_logging_and_milestones(self):
        # Reset milestones for test
        if os.path.exists("data/unlocked_milestones.json"):
            try:
                os.remove("data/unlocked_milestones.json")
            except Exception:
                pass
                
        # Log a timeline event that triggers a milestone (e.g. started learning)
        log_timeline_event(
            title="Started learning Python",
            source="document_pdf",
            metadata={"concept": "Python"}
        )
        
        timeline = load_timeline()
        self.assertEqual(len(timeline), 1)
        self.assertEqual(timeline[0]["title"], "Started learning Python")
        self.assertEqual(timeline[0]["source"], "document_pdf")
        
        # Verify milestone unlocked
        milestones = load_unlocked_milestones()
        self.assertIn("Started learning Python", milestones)

    @patch('ai.gateway.broker.AIGateway.generate_response')
    def test_memory_manager_commit(self, mock_generate):
        # Mock importance score to be low (0.1) so it doesn't trigger async extractors
        mock_generate.return_value = "0.1"
        
        # Commit turn
        evaluate_and_commit("hello buddy", "hey developer", "neutral")
        
        # Verify added to working memory
        memory = load_working_memory()
        self.assertEqual(len(memory), 1)
        self.assertEqual(memory[0]["user"], "hello buddy")
        self.assertEqual(memory[0]["bot"], "hey developer")

if __name__ == "__main__":
    unittest.main()

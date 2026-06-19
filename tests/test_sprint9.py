import os
import sys
import unittest
import time
from unittest.mock import MagicMock, patch

# Add workspace root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from memory.user_profile import load_profile, save_profile, update_profile_field
from events.bus import global_bus
from core.activity import check_struggle, key_history

class TestSprint9(unittest.TestCase):
    
    def setUp(self):
        # Clear key history
        key_history.clear()
        # Clear event bus subscribers to prevent background task pollution
        global_bus._subscribers.clear()
        
    def test_profile_load_save(self):
        # Verify load_profile returns default structure if no file
        profile = load_profile()
        self.assertIn("name", profile)
        self.assertIn("timezone", profile)
        self.assertIn("is_student", profile)
        self.assertIn("goals", profile)
        
        # Test save and update
        save_profile(profile)
        update_profile_field("name", "Test User")
        
        new_profile = load_profile()
        self.assertEqual(new_profile["name"], "Test User")
        
        # Reset name
        update_profile_field("name", "Developer")

    @patch('ai.gateway.broker.AIGateway.generate_response')
    def test_profile_extraction(self, mock_generate):
        # Mock LLM JSON response
        mock_generate.return_value = '{"name": "Alice", "college": "Stanford", "is_student": true}'
        
        from memory.user_profile import _extract_profile_job
        _extract_profile_job("Hi Daemon, my name is Alice and I go to Stanford.")
        
        profile = load_profile()
        self.assertEqual(profile["name"], "Alice")
        self.assertEqual(profile["college"], "Stanford")
        self.assertTrue(profile["is_student"])
        
        # Cleanup
        update_profile_field("name", "Developer")
        update_profile_field("college", "None")
        update_profile_field("is_student", False)

    def test_struggle_detector(self):
        # Mock event bus handler
        struggle_triggered = []
        
        def handle_struggle(event):
            struggle_triggered.append(event)
            
        global_bus.subscribe("user_struggling", handle_struggle)
        
        # Simulate typing: 10 regular keypresses, then 15 deletions (total 25, 15 deletes = 60% ratio)
        from collections import namedtuple
        KeyMock = namedtuple("KeyMock", ["name"])
        backspace_key = KeyMock("backspace")
        regular_key = KeyMock("a")
        
        # We need to simulate these in check_struggle
        # We reset last_struggle_time to 0 to ensure no cooldown issues
        import core.activity
        core.activity.last_struggle_time = 0.0
        
        # 10 regular keys
        for _ in range(10):
            check_struggle(regular_key)
            
        # 15 deletes
        for _ in range(15):
            check_struggle(backspace_key)
            
        # Verify event was published
        self.assertTrue(len(struggle_triggered) > 0, "Struggle event was not triggered!")
        event = struggle_triggered[0]
        self.assertEqual(event.name, "user_struggling")
        self.assertGreater(event.payload["delete_ratio"], 0.40)
        
        # Cleanup subscription
        global_bus.unsubscribe("user_struggling", handle_struggle)

if __name__ == "__main__":
    unittest.main()

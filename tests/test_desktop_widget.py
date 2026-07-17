import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add root folder to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from interfaces.desktop_widget import CompanionApp, KIVY_AVAILABLE
from events.bus import global_bus, Event

class TestDesktopWidget(unittest.TestCase):
    
    def setUp(self):
        self.app = CompanionApp()

    def test_widget_initialization(self):
        self.assertEqual(self.app.current_state, "idle")
        self.assertEqual(self.app.frame_index, 0)
        self.assertTrue("Initializing" in self.app.active_goal)

    def test_task_started_updates_ui(self):
        event = Event("task_started", "test_sender", {"task_name": "Implement Database routing"})
        global_bus.publish(event)
        
        self.assertEqual(self.app.current_state, "thinking")
        self.assertEqual(self.app.active_goal, "Working on: Implement Database routing")
        if KIVY_AVAILABLE and self.app.label_widget:
            self.assertEqual(self.app.label_widget.text, "Working on: Implement Database routing")

    def test_user_struggling_updates_ui(self):
        event = Event("user_struggling", "test_sender", {})
        global_bus.publish(event)
        
        self.assertEqual(self.app.current_state, "struggling")
        self.assertEqual(self.app.active_goal, "Need help? Let's check the code!")
        if KIVY_AVAILABLE and self.app.label_widget:
            self.assertEqual(self.app.label_widget.text, "Need help? Let's check the code!")

    def test_personality_update_updates_ui(self):
        event = Event("personality_update", "test_sender", {"sprite_state": "happy"})
        global_bus.publish(event)
        
        self.assertEqual(self.app.current_state, "happy")

    def test_animate_tick_increments_frames(self):
        initial_frame_index = self.app.frame_index
        
        if KIVY_AVAILABLE:
            self.app.animate_tick(0.25)
        else:
            self.app.animate_tick()
            
        self.assertEqual(self.app.frame_index, initial_frame_index + 1)

if __name__ == "__main__":
    unittest.main()

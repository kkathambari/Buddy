import os
import sys
import unittest
import time
from unittest.mock import MagicMock, patch

# Add workspace root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from relationship.bond import get_attachment_style, get_relationship_level, calculate_bond_increment
from relationship.trust import get_proactivity_level, is_proactive_allowed
from relationship.personality import adjust_personality_modifiers
from relationship.manager import get_relationship, update_relationship, load_relationship_data, save_relationship_data
from proactive.cooldowns import is_cooldown_active, update_cooldown, reset_cooldown
from proactive.priority import get_event_priority, ProactivePriority
from proactive.scheduler import schedule_reminder
from proactive.trigger import proactive_queue, handle_user_struggling, handle_category_changed
from brain.reflection import SelfReflection
from brain.conversation import process_chat, _pending_feedback
from events.bus import Event, global_bus
from brain.decision_engine import global_decision_engine

class TestRelationshipProactive(unittest.TestCase):

    def setUp(self):
        # Ensure user profile name is not default to prevent onboarding intercept
        from memory.user_profile import update_profile_field
        update_profile_field("name", "Alice")
        
        # Clear relationship file and pending feedbacks
        if os.path.exists("data/relationship.json"):
            try:
                os.remove("data/relationship.json")
            except Exception:
                pass
        _pending_feedback.clear()
        # Reset queues
        while not proactive_queue.empty():
            try:
                proactive_queue.get_nowait()
            except Exception:
                pass
        # Reset cooldowns
        reset_cooldown("user_struggling")
        reset_cooldown("active_category_changed")

    def tearDown(self):
        from memory.user_profile import update_profile_field
        update_profile_field("name", "Developer")
        
        if os.path.exists("data/relationship.json"):
            try:
                os.remove("data/relationship.json")
            except Exception:
                pass

    def test_bond_calculations(self):
        self.assertEqual(get_attachment_style(5), "neutral")
        self.assertEqual(get_attachment_style(25), "warm")
        self.assertEqual(get_attachment_style(50), "attached")

        self.assertEqual(get_relationship_level(5), "stranger")
        self.assertEqual(get_relationship_level(20), "familiar")
        self.assertEqual(get_relationship_level(40), "friend")
        self.assertEqual(get_relationship_level(80), "close")

        self.assertEqual(calculate_bond_increment(True), 2)
        self.assertEqual(calculate_bond_increment(False), -1)
        self.assertEqual(calculate_bond_increment(True, 2.0), 4)

    def test_trust_proactivity_gates(self):
        self.assertEqual(get_proactivity_level(0.2), "quiet")
        self.assertEqual(get_proactivity_level(0.5), "moderate")
        self.assertEqual(get_proactivity_level(0.9), "high")

        # Quiet trust allows no proactivity
        self.assertFalse(is_proactive_allowed(0.2, "focus_reminder"))
        
        # Moderate trust allows focus reminders only if session is >= 2 hours (7200s)
        self.assertFalse(is_proactive_allowed(0.5, "focus_reminder", 3600.0))
        self.assertTrue(is_proactive_allowed(0.5, "focus_reminder", 7500.0))
        self.assertFalse(is_proactive_allowed(0.5, "other_event"))

        # High trust allows everything
        self.assertTrue(is_proactive_allowed(0.8, "focus_reminder", 100.0))
        self.assertTrue(is_proactive_allowed(0.8, "quiz_trigger"))

    def test_personality_adjustment(self):
        base_stats = {"snark": 50, "wisdom": 50, "energy": 50}
        
        # Low trust -> higher snark, lower wisdom
        adjusted_low = adjust_personality_modifiers(base_stats, 0.2, 0)
        self.assertGreater(adjusted_low["snark"], 50)
        self.assertLess(adjusted_low["wisdom"], 50)

        # High trust -> lower snark, higher wisdom
        adjusted_high = adjust_personality_modifiers(base_stats, 0.9, 0)
        self.assertLess(adjusted_high["snark"], 50)
        self.assertGreater(adjusted_high["wisdom"], 50)

        # High bond -> higher energy
        adjusted_bond = adjust_personality_modifiers(base_stats, 0.5, 60)
        self.assertGreater(adjusted_bond["energy"], 50)

    def test_relationship_manager(self):
        # Event Bus subscription check
        events = []
        def handler(event):
            events.append(event)
        global_bus.subscribe("relationship_changed", handler)

        # Test initial load
        rel = get_relationship("test_comp")
        self.assertEqual(rel["trust"], 0.5)
        self.assertEqual(rel["bond"], 0)

        # Test update
        rel = update_relationship("test_comp", 0.2, 15, "Test interaction")
        self.assertAlmostEqual(rel["trust"], 0.7)
        self.assertEqual(rel["bond"], 15)
        self.assertEqual(rel["attachment_style"], "warm")
        self.assertTrue(len(rel["history"]) > 0)
        self.assertEqual(rel["history"][0]["action"], "Test interaction")

        # Test event was published
        self.assertTrue(len(events) > 0)
        self.assertEqual(events[0].payload["companion_id"], "test_comp")
        self.assertAlmostEqual(events[0].payload["trust"], 0.7)
        self.assertEqual(events[0].payload["bond"], 15)

        global_bus.unsubscribe("relationship_changed", handler)

    def test_proactive_cooldowns(self):
        self.assertFalse(is_cooldown_active("user_struggling"))
        update_cooldown("user_struggling")
        self.assertTrue(is_cooldown_active("user_struggling"))
        reset_cooldown("user_struggling")
        self.assertFalse(is_cooldown_active("user_struggling"))

    def test_proactive_priorities(self):
        self.assertEqual(get_event_priority("focus_reminder"), ProactivePriority.HIGH)
        self.assertEqual(get_event_priority("milestone_unlocked"), ProactivePriority.MEDIUM)
        self.assertEqual(get_event_priority("random_comment"), ProactivePriority.LOW)

    @patch('ai.gateway.broker.AIGateway.generate_response')
    def test_proactive_trigger_and_scheduler(self, mock_generate):
        mock_generate.return_value = "Mocked Proactive Comment"
        
        # Test struggle trigger
        event = Event("user_struggling", "activity_hooks", {"delete_ratio": 0.5})
        handle_user_struggling(event)
        self.assertFalse(proactive_queue.empty())
        msg = proactive_queue.get_nowait()
        self.assertEqual(msg, "Mocked Proactive Comment")

        # Test category switch trigger
        event_cat = Event("active_category_changed", "activity_hooks", {"new_category": "coding", "title": "test"})
        handle_category_changed(event_cat)
        self.assertFalse(proactive_queue.empty())
        msg = proactive_queue.get_nowait()
        self.assertEqual(msg, "Mocked Proactive Comment")

        # Test Scheduler
        timer = schedule_reminder("test_alert", 0.01, "Test Alert Prompt")
        # Wait up to 2 seconds for the background timer thread to execute
        start_time = time.time()
        while proactive_queue.empty() and (time.time() - start_time) < 2.0:
            time.sleep(0.01)
        self.assertFalse(proactive_queue.empty(), "Scheduler reminder was not queued!")
        msg_timer = proactive_queue.get_nowait()
        self.assertEqual(msg_timer, "Mocked Proactive Comment")

    def test_sentiment_evaluation(self):
        self.assertTrue(SelfReflection.evaluate_feedback("yes indeed"))
        self.assertTrue(SelfReflection.evaluate_feedback("worked perfectly, thank you"))
        self.assertFalse(SelfReflection.evaluate_feedback("no, didn't work"))
        self.assertFalse(SelfReflection.evaluate_feedback("nope, still broken"))

    @patch('ai.gateway.broker.AIGateway.generate_response')
    def test_conversation_reflection_intercept(self, mock_generate):
        mock_generate.return_value = "Normal response"
        
        # Setup finished session in EducationCapability
        from capabilities.education.handler import EducationCapability
        edu_cap = EducationCapability()
        edu_cap._active_sessions["test_companion"] = {"concept": "Python", "stage": "complete"}
        global_decision_engine.register_capability("education", edu_cap)

        # Call process_chat when capability just completed
        res, _ = process_chat("my answer", {"snark": 50}, 100, "test_companion")
        self.assertIn("Did I help you get that working?", res)
        # Should populate _pending_feedback
        self.assertIn("test_companion", _pending_feedback)
        self.assertEqual(_pending_feedback["test_companion"]["capability"], "education")

        # Call process_chat to verify positive feedback intercept
        res_fb, _ = process_chat("yes, it worked!", {"snark": 50}, 100, "test_companion")
        self.assertIn("I'm glad to hear that", res_fb)
        # Pending feedback should be cleared
        self.assertNotIn("test_companion", _pending_feedback)
        
        # Verify relationship metrics updated positively
        rel = get_relationship("test_companion")
        self.assertGreater(rel["trust"], 0.5)
        self.assertGreater(rel["bond"], 0)

        # Test negative feedback intercept
        # Setup finished session again
        edu_cap._active_sessions["test_companion"] = {"concept": "Python", "stage": "complete"}
        res2, _ = process_chat("another answer", {"snark": 50}, 100, "test_companion")
        self.assertIn("Did I help you get that working?", res2)
        
        # Call process_chat to verify negative feedback intercept
        res_fb2, _ = process_chat("no, still broken", {"snark": 50}, 100, "test_companion")
        self.assertIn("I appreciate the feedback", res_fb2)
        
        # Verify relationship metrics decayed
        rel2 = get_relationship("test_companion")
        # Trust should be back to original or lower because of decay
        self.assertLess(rel2["trust"], rel["trust"])

if __name__ == "__main__":
    unittest.main()

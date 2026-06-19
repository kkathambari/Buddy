import os
import sys
import unittest
import time
from unittest.mock import MagicMock, patch

# Add workspace root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.feature_flags import FeatureFlags
from core.analytics import ProductAnalytics
from brain.attention import AttentionEngine
from brain.experience import ExperienceEngine
from brain.decision_engine import DecisionEngine
from brain.intent_types import Intent, IntentCategory
from brain.conversation import process_chat
from memory.user_profile import load_profile, update_profile_field
from relationship.manager import get_relationship, update_relationship
from memory.semantic import store_memory, retrieve_shared_memories, VECTOR_DB_PATH

class TestProductExperience(unittest.TestCase):
    
    def setUp(self):
        # Reset state files and caches
        FeatureFlags.reset_defaults()
        ProductAnalytics.clear_events()
        ExperienceEngine.clear_state()
        
        # Save current profile name/goals so we can restore them
        self.original_profile = load_profile()
        update_profile_field("name", "Test User") # Ensure not default during setup
        
        # Clean vectors database path if exists
        if os.path.exists(VECTOR_DB_PATH):
            try:
                os.remove(VECTOR_DB_PATH)
            except Exception:
                pass
                
        # Enable multi-signal checking mode for this test suite
        import core.activity
        core.activity.testing_mode = "multi_signal"
        
    def tearDown(self):
        # Restore profile
        update_profile_field("name", self.original_profile.get("name", "Developer"))
        update_profile_field("goals", self.original_profile.get("goals", []))
        ProductAnalytics.clear_events()
        ExperienceEngine.clear_state()
        FeatureFlags.reset_defaults()
        if os.path.exists(VECTOR_DB_PATH):
            try:
                os.remove(VECTOR_DB_PATH)
            except Exception:
                pass
                
        # Reset testing mode
        import core.activity
        core.activity.testing_mode = None

    def test_relationship_parameters(self):
        # Verify defaults
        rel = get_relationship("test_growth")
        self.assertEqual(rel["respect"], 0.5)
        self.assertEqual(rel["confidence"], 0.5)
        self.assertEqual(rel["growth_stage"], "month_1_careful")
        
        # Verify updates
        updated_rel = update_relationship("test_growth", 0.0, 120, "Finished milestone project", respect_change=0.2, confidence_change=0.3)
        self.assertAlmostEqual(updated_rel["respect"], 0.7)
        self.assertAlmostEqual(updated_rel["confidence"], 0.8)
        self.assertEqual(updated_rel["growth_stage"], "month_3_playful")

    def test_feature_flags(self):
        # Default flags should be true
        self.assertTrue(FeatureFlags.is_enabled("education"))
        self.assertTrue(FeatureFlags.is_enabled("attention_engine"))
        
        # Toggle flag
        FeatureFlags.set_flag("education", False)
        self.assertFalse(FeatureFlags.is_enabled("education"))
        
        # Test routing in DecisionEngine with flag disabled
        engine = DecisionEngine()
        intent = Intent(IntentCategory.LEARNING, "let's study python", 1.0, {"concept": "python"})
        response = engine.execute(intent, {}, 100)
        self.assertEqual(response, "The Education Capability is currently disabled.")

    def test_product_analytics(self):
        # Verify empty initially
        self.assertEqual(len(ProductAnalytics.get_events()), 0)
        
        # Log event
        ProductAnalytics.track_event("test_event", {"metric": 42})
        events = ProductAnalytics.get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "test_event")
        self.assertEqual(events[0]["metadata"]["metric"], 42)
        
        # Clear
        ProductAnalytics.clear_events()
        self.assertEqual(len(ProductAnalytics.get_events()), 0)

    def test_attention_engine_keywords(self):
        # Check topic detection and focus extraction
        attn = AttentionEngine.determine_attention("I want to study databases and sql coding")
        self.assertEqual(attn["primary_focus"], "learning")
        self.assertIn("databases", attn["focus_keywords"])
        self.assertEqual(attn["memory_limit"], 2)
        
        # Emotion detection
        attn_emo = AttentionEngine.determine_attention("I am feeling very tired and sad today")
        self.assertEqual(attn_emo["primary_focus"], "emotion")
        self.assertIn("tired", attn_emo["focus_keywords"])
        self.assertEqual(attn_emo["memory_limit"], 1)

    def test_attention_flag_disabled(self):
        # Disable attention engine
        FeatureFlags.set_flag("attention_engine", False)
        attn = AttentionEngine.determine_attention("I want to study databases")
        self.assertEqual(attn["memory_limit"], 5)
        self.assertEqual(attn["focus_keywords"], ["I want to study databases"])

    def test_experience_engine_onboarding_script_complete(self):
        # Force default profile settings to trigger onboarding
        update_profile_field("name", "Developer")
        
        # 1. Trigger onboarding
        trigger_resp = ExperienceEngine.intercept("hello companion")
        self.assertEqual(trigger_resp, "Hi... I'm Daemon. So... what brings you here?")
        
        # 2. Natural complete message with both name and goal
        response = ExperienceEngine.intercept("I am Bob and I am learning Python")
        self.assertIsNotNone(response)
        self.assertIn("Nice to meet you, Bob.", response)
        self.assertIn("Sticking with Python?", response)
        self.assertEqual(load_profile()["name"], "Bob")
        
        # Verify onboarding completed immediately
        self.assertIsNone(ExperienceEngine.intercept("hello"))

    def test_experience_engine_onboarding_script_incomplete(self):
        update_profile_field("name", "Developer")
        
        # 1. Trigger onboarding
        trigger_resp = ExperienceEngine.intercept("hello companion")
        self.assertEqual(trigger_resp, "Hi... I'm Daemon. So... what brings you here?")
        
        # 2. Name only
        response1 = ExperienceEngine.intercept("my name is Alice")
        self.assertIsNotNone(response1)
        self.assertIn("Nice to meet you, Alice. What is your primary programming language or goal right now?", response1)
        self.assertEqual(load_profile()["name"], "Alice")
        
        # 3. Goal follow-up
        response2 = ExperienceEngine.intercept("rust coding")
        self.assertIsNotNone(response2)
        self.assertIn("Got it, Alice. Sticking with your goals. Let's get to work!", response2)
        
        # Completed
        self.assertIsNone(ExperienceEngine.intercept("hello"))

    @patch('core.activity.get_active_window_title')
    def test_multi_signal_struggle_checking(self, mock_title):
        mock_title.return_value = "main.py"
        
        from core.activity import check_struggle, key_history, typing_state, last_struggle_time
        key_history.clear()
        
        # Mock struggle callback
        struggles = []
        def on_struggle(event):
            struggles.append(event)
        
        from events.bus import global_bus
        global_bus.subscribe("user_struggling", on_struggle)
        
        # 1. Test struggle does NOT trigger if deletes are high but file duration is short
        now = time.time()
        typing_state["active_file_start_time"] = now # short file duration
        typing_state["last_save_time"] = now
        typing_state["last_compile_time"] = now
        
        class KeyMock:
            name = "backspace"
            
        for _ in range(25):
            check_struggle(KeyMock())
            
        self.assertEqual(len(struggles), 0)
        
        # 2. Set signals to indicate stuck state
        typing_state["active_file_start_time"] = now - 600.0 # 10 mins on same file
        typing_state["last_save_time"] = now - 600.0 # 10 mins without save
        typing_state["last_compile_time"] = now - 600.0 # 10 mins without compile
        
        # Reset cooldown and history
        key_history.clear()
        import core.activity
        core.activity.last_struggle_time = 0.0
        
        for _ in range(25):
            check_struggle(KeyMock())
            
        self.assertTrue(len(struggles) > 0)
        global_bus.unsubscribe("user_struggling", on_struggle)

    @patch('memory.semantic.get_embedding')
    def test_shared_memory_flag(self, mock_embed):
        mock_embed.return_value = [0.1, 0.2, 0.3]
        
        # Store memory with shared metadata
        store_memory("We fixed the VivaForge quiz bug together!", importance=0.9, emotion="happy", shared=True)
        
        # Retrieve shared memories
        shared = retrieve_shared_memories(1)
        self.assertEqual(len(shared), 1)
        self.assertIn("VivaForge quiz bug", shared[0])

    @patch('ai.gateway.broker.AIGateway.generate_response')
    def test_cognitive_reasoner_attention_filtering(self, mock_generate):
        mock_generate.return_value = "Mocked Response"
        
        from brain.reasoner import CognitiveReasoner
        with patch('brain.attention.AttentionEngine.determine_attention') as mock_attn:
            mock_attn.return_value = {
                "primary_focus": "learning",
                "focus_keywords": ["python"],
                "memory_limit": 2,
                "attention_level": 0.8
            }
            
            CognitiveReasoner.reason({"raw_text": "tell me about python databases", "tone": {"emotion": "neutral", "intensity": "low"}, "emotion": "neutral"}, {}, 100)
            mock_attn.assert_called_once()

if __name__ == "__main__":
    unittest.main()

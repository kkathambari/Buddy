import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add workspace root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from brain.intent import detect_intent
from brain.intent_types import IntentCategory
from brain.decision_engine import global_decision_engine, DecisionEngine

class TestBrainPipeline(unittest.TestCase):
    
    def test_intent_matching_rules(self):
        # Greetings
        self.assertEqual(detect_intent("hello").category, IntentCategory.GREETING)
        self.assertEqual(detect_intent("good morning buddy").category, IntentCategory.GREETING)
        
        # Learning triggers
        learning_intent = detect_intent("I want to study python algorithms")
        self.assertEqual(learning_intent.category, IntentCategory.LEARNING)
        self.assertEqual(learning_intent.entities.get("concept"), "Python")
        
        # Career triggers
        career_intent = detect_intent("review my resume for a backend internship")
        self.assertEqual(career_intent.category, IntentCategory.CAREER)
        self.assertEqual(career_intent.entities.get("role"), "Backend Developer")
        
        # Productivity query
        self.assertEqual(detect_intent("show my coding hours stats").category, IntentCategory.PRODUCTIVITY_QUERY)
        
        # Memory query
        self.assertEqual(detect_intent("do you remember my favorite IDE?").category, IntentCategory.MEMORY_QUERY)
        
        # Emotion logs
        emo_intent = detect_intent("feeling tired and frustrated today")
        self.assertEqual(emo_intent.category, IntentCategory.EMOTION)
        self.assertEqual(emo_intent.entities.get("emotion"), "tired")
        
        # System commands
        self.assertEqual(detect_intent("[OPEN: chrome]").category, IntentCategory.SYSTEM_COMMAND)
        self.assertEqual(detect_intent("/exit").category, IntentCategory.SYSTEM_COMMAND)
        
        # Companionship fallback
        self.assertEqual(detect_intent("what is the weather like?").category, IntentCategory.COMPANIONSHIP)

    @patch('brain.reasoner.CognitiveReasoner.reason')
    def test_decision_engine_routing(self, mock_reason):
        # Setup mock capability
        mock_handler = MagicMock()
        mock_handler.return_value = "Mock Capability response"
        
        engine = DecisionEngine()
        engine.register_capability("education", mock_handler)
        
        # Test routing to registered capability
        intent = detect_intent("let's study databases")
        response = engine.execute(intent, {}, 100)
        self.assertEqual(response, "Mock Capability response")
        mock_handler.assert_called_once()
        
        # Test routing to greetings rule
        greeting_intent = detect_intent("hey buddy")
        greeting_resp = engine.execute(greeting_intent, {}, 100)
        self.assertTrue(any(g in greeting_resp for g in [
            "Hey there", "Hey. Ready", "Waking up", "hello. Back"
        ]))
        
        # Test routing to fallback reasoner
        mock_reason.return_value = "Mock Reasoner response"
        companionship_intent = detect_intent("let's talk about ghosts")
        fallback_resp = engine.execute(companionship_intent, {"wisdom": 50}, 80)
        self.assertEqual(fallback_resp, "Mock Reasoner response")
        mock_reason.assert_called_once()

if __name__ == "__main__":
    unittest.main()

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add workspace root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from events.bus import Event, global_bus
from brain.decision_engine import DecisionEngine
from capabilities.base import Capability
from capabilities.education.handler import EducationCapability
from capabilities.career.handler import CareerCapability

class TestCapabilityBus(unittest.TestCase):
    
    def test_event_payload_structure(self):
        # Create a test event
        payload = {"key": "value"}
        event = Event(name="test_event", sender="test_sender", payload=payload)
        
        # Verify fields
        self.assertIsNotNone(event.event_id)
        self.assertTrue(len(event.event_id) > 0)
        # Should be a UUID string
        import uuid
        try:
            val = uuid.UUID(event.event_id, version=4)
        except ValueError:
            self.fail("event_id is not a valid UUIDv4")
            
        self.assertEqual(event.name, "test_event")
        self.assertEqual(event.sender, "test_sender")
        self.assertEqual(event.payload, payload)
        self.assertIsNotNone(event.timestamp)
        # Verify it's an ISO-8601 string
        from datetime import datetime
        try:
            datetime.fromisoformat(event.timestamp)
        except ValueError:
            self.fail("timestamp is not a valid ISO-8601 string")

    def test_event_bus_pub_sub(self):
        received_events = []
        def callback(event):
            received_events.append(event)
            
        global_bus.subscribe("bus_test_event", callback)
        event = Event(name="bus_test_event", sender="test_sender", payload={"foo": "bar"})
        
        # Publish synchronously
        global_bus.publish(event, async_mode=False)
        
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].name, "bus_test_event")
        self.assertEqual(received_events[0].sender, "test_sender")
        self.assertEqual(received_events[0].payload["foo"], "bar")
        
        # Unsubscribe and publish again
        global_bus.unsubscribe("bus_test_event", callback)
        global_bus.publish(event, async_mode=False)
        self.assertEqual(len(received_events), 1)

    def test_decision_engine_validation(self):
        engine = DecisionEngine()
        
        # Registering an invalid capability type (e.g. not inheriting from Capability)
        with self.assertRaises(TypeError):
            engine.register_capability("invalid_cap", "not_a_capability_instance") # type: ignore
            
        # Registering a valid capability (mock class inheriting from Capability)
        class DummyCapability(Capability):
            def initialize(self) -> None: pass
            def observe(self, context) -> None: pass
            def execute(self, intent, stats, energy) -> str: return "dummy"
            def reflect(self) -> dict: return {}
            def update_memory(self) -> None: pass
            def shutdown(self) -> None: pass
            
        dummy = DummyCapability()
        engine.register_capability("dummy_cap", dummy)
        self.assertIn("dummy_cap", engine._capabilities)

    @patch('ai.gateway.broker.AIGateway.generate_response')
    def test_education_capability_lifecycle(self, mock_generate):
        mock_generate.return_value = "Mock Tutor Response"
        
        cap = EducationCapability()
        
        # Lifecycle calls
        cap.initialize()
        cap.observe({"active_window": "VS Code"})
        
        # Test execute start study session
        intent = {
            "category": "capability_execution",
            "capability": "education",
            "raw_text": "start session python",
            "entities": {"concept": "python"},
            "companion_id": "test_companion"
        }
        res = cap.execute(intent, {}, 100)
        self.assertIn("Let's study Python", res)
        self.assertIn("test_companion", cap._active_sessions)
        self.assertEqual(cap._active_sessions["test_companion"]["concept"], "Python")
        self.assertEqual(cap._active_sessions["test_companion"]["stage"], "viva_questioning")
        
        # Test execute viva questioning
        intent_answer = {
            "category": "capability_execution",
            "capability": "education",
            "raw_text": "it's for writing scripts",
            "entities": {},
            "companion_id": "test_companion"
        }
        res_viva = cap.execute(intent_answer, {}, 100)
        self.assertEqual(res_viva, "Mock Tutor Response")
        
        # Reflection, memory, shutdown
        refl = cap.reflect()
        self.assertIn("trust_increment", refl)
        self.assertIn("bond_points", refl)
        
        cap.update_memory()
        cap.shutdown()

    @patch('ai.gateway.broker.AIGateway.generate_response')
    def test_career_capability_lifecycle(self, mock_generate):
        mock_generate.return_value = "Mock Coach Response"
        
        cap = CareerCapability()
        
        # Lifecycle calls
        cap.initialize()
        cap.observe({"active_window": "VS Code"})
        
        # Test execute start career discussion
        intent = {
            "category": "capability_execution",
            "capability": "career",
            "raw_text": "help me with my career",
            "entities": {},
            "companion_id": "test_companion"
        }
        res = cap.execute(intent, {}, 100)
        self.assertIn("What kind of role or internship are we targeting", res)
        self.assertIn("test_companion", cap._active_career_sessions)
        
        # Profile step: select role
        intent_role = {
            "category": "capability_execution",
            "capability": "career",
            "raw_text": "backend",
            "entities": {},
            "companion_id": "test_companion"
        }
        res_role = cap.execute(intent_role, {}, 100)
        self.assertIn("Paste your resume summary here", res_role)
        self.assertEqual(cap._active_career_sessions["test_companion"]["stage"], "ats_review")
        
        # ATS review step: submit resume info
        intent_resume = {
            "category": "capability_execution",
            "capability": "career",
            "raw_text": "python sql git",
            "entities": {},
            "companion_id": "test_companion"
        }
        res_resume = cap.execute(intent_resume, {}, 100)
        self.assertIn("ATS matching algorithm", res_resume)
        self.assertEqual(cap._active_career_sessions["test_companion"]["stage"], "mock_interview")
        
        # Mock Interview step: answer question
        intent_answer = {
            "category": "capability_execution",
            "capability": "career",
            "raw_text": "I fixed a deadlock in python",
            "entities": {},
            "companion_id": "test_companion"
        }
        res_answer = cap.execute(intent_answer, {}, 100)
        self.assertIn("Mock Coach Response", res_answer)
        self.assertEqual(cap._active_career_sessions["test_companion"]["stage"], "complete")
        
        # Reflection, memory, shutdown
        refl = cap.reflect()
        self.assertIn("trust_increment", refl)
        self.assertIn("bond_points", refl)
        
        cap.update_memory()
        cap.shutdown()

if __name__ == "__main__":
    unittest.main()

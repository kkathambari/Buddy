import os
import sys
import unittest
import asyncio
import time
from unittest.mock import MagicMock, patch

# Add root folder to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from brain.dream import DreamEngine
from memory.knowledge_graph import KnowledgeGraphManager
from memory.working_memory import add_dialog_turn
from events.bus import global_bus, Event
from core.runtime import global_runtime

class TestDreamMode(unittest.TestCase):
    
    def setUp(self):
        self.test_db_file = "data/test_knowledge_graph_dream.db"
        if os.path.exists(self.test_db_file):
            try:
                os.remove(self.test_db_file)
            except OSError:
                pass
                
        self.engine = DreamEngine(db_path=self.test_db_file)

    def tearDown(self):
        if os.path.exists(self.test_db_file):
            try:
                os.remove(self.test_db_file)
            except OSError:
                pass

    def test_memory_consolidation_from_chat_history(self):
        # 1. Add mock interactions detailing declarations to working memory
        add_dialog_turn("Alice is a student at Stanford. Bob is a teacher.", "Logged and noted.", "neutral")
        
        # 2. Run memory consolidation
        count = self.engine.consolidate_memories()
        self.assertTrue(count >= 2)
        
        # 3. Verify graph node details
        node_alice = self.engine.kg.get_node("user_alice")
        self.assertIsNotNone(node_alice)
        self.assertEqual(node_alice["name"], "Alice")
        self.assertEqual(node_alice["properties"].get("role"), "student at Stanford")
        
        node_bob = self.engine.kg.get_node("user_bob")
        self.assertIsNotNone(node_bob)
        self.assertEqual(node_bob["properties"].get("role"), "teacher")

    def test_database_vacuum_optimization(self):
        # Build mock data to vacuum
        self.engine.kg.add_node("dummy", "meta", "dummy", {})
        
        # Run optimization
        success = self.engine.optimize_database()
        self.assertTrue(success)

    def test_event_bus_idle_dream_cycle_scheduling(self):
        # Mock dream cycle execution
        with patch('brain.dream.DreamEngine.start_dream_cycle') as mock_cycle:
            mock_cycle.return_value = "Mocked Consolidation."
            
            # Fire event on event bus
            global_bus.publish(Event("user_idle", "test", {}))
            
            # Allow event thread/scheduler to execute task
            time.sleep(0.3)
            
            mock_cycle.assert_called()

if __name__ == "__main__":
    unittest.main()

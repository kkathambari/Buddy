import os
import sys
import unittest
import shutil

# Resolve workspace root
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.config import set_config, get_config
from backend.repositories.sqlite import SqliteCompanionRepository, SqliteMemoryRepository, DB_PATH
from backend.repositories.firebase import FirebaseCompanionRepository, FirebaseMemoryRepository
from backend.repositories.factory import get_companion_repository, get_memory_repository

class TestRepositories(unittest.TestCase):

    def setUp(self):
        # Save original config
        self.original_config = get_config()
        # Clean up database if exists to start fresh
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception:
                pass
        # Re-initialize SQLite repo by forcing database schema creation
        from backend.repositories.sqlite import init_db
        init_db()

    def tearDown(self):
        # Restore original config
        for k, v in self.original_config.items():
            set_config(k, v)
        # Clean database file
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception:
                pass

    def test_sqlite_companion_repository(self):
        repo = SqliteCompanionRepository()
        companion_id = "test_companion_123"
        
        # Verify get returns None on non-existent id
        self.assertIsNone(repo.get(companion_id))
        
        # Save mock companion soul data
        test_data = {
            "name": "GhostBuddy",
            "energy": 85.5,
            "rarity": "rare",
            "alive": True,
            "is_first_run": False,
            "stats": {
                "bond": 12,
                "trust": 0.8,
                "respect": 0.7,
                "confidence": 0.6,
                "growth_stage": "month_3_playful"
            }
        }
        self.assertTrue(repo.save(companion_id, test_data))
        
        # Retrieve and verify
        retrieved = repo.get(companion_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["name"], "GhostBuddy")
        self.assertEqual(retrieved["energy"], 85.5)
        self.assertEqual(retrieved["rarity"], "rare")
        self.assertTrue(retrieved["alive"])
        self.assertFalse(retrieved["is_first_run"])
        self.assertEqual(retrieved["stats"]["bond"], 12)
        self.assertEqual(retrieved["stats"]["trust"], 0.8)
        self.assertEqual(retrieved["stats"]["respect"], 0.7)
        self.assertEqual(retrieved["stats"]["confidence"], 0.6)
        self.assertEqual(retrieved["stats"]["growth_stage"], "month_3_playful")
        
        # Test get_stats helper
        stats = repo.get_stats(companion_id)
        self.assertEqual(stats["bond"], 12)
        
        # Delete and verify
        self.assertTrue(repo.delete(companion_id))
        self.assertIsNone(repo.get(companion_id))

    def test_sqlite_memory_repository(self):
        repo = SqliteMemoryRepository()
        session_id = "chat_session_456"
        
        # Fetching non-existent returns empty list
        self.assertEqual(repo.get(session_id), [])
        
        # Save messages list
        chat_logs = [
            {"sender": "user", "message": "Hi, who are you?", "timestamp": 100.0},
            {"sender": "pet", "message": "I'm Daemon, your ghostly guide.", "timestamp": 101.0},
            {"sender": "user", "message": "Can you help me learn Python?", "timestamp": 102.0}
        ]
        self.assertTrue(repo.save(session_id, chat_logs))
        
        # Retrieve complete history
        retrieved = repo.get(session_id)
        self.assertEqual(len(retrieved), 3)
        self.assertEqual(retrieved[0]["sender"], "user")
        self.assertEqual(retrieved[0]["message"], "Hi, who are you?")
        self.assertEqual(retrieved[2]["message"], "Can you help me learn Python?")
        
        # Test get_recent_history limit
        recent = repo.get_recent_history(session_id, limit=2)
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["sender"], "pet")
        self.assertEqual(recent[1]["sender"], "user")
        
        # Delete and verify
        self.assertTrue(repo.delete(session_id))
        self.assertEqual(repo.get(session_id), [])

    def test_repository_factory_selection(self):
        # Set config to sqlite
        set_config("repository_type", "sqlite")
        comp_repo = get_companion_repository()
        mem_repo = get_memory_repository()
        self.assertIsInstance(comp_repo, SqliteCompanionRepository)
        self.assertIsInstance(mem_repo, SqliteMemoryRepository)
        
        # Set config to firebase
        set_config("repository_type", "firebase")
        comp_repo_fb = get_companion_repository()
        mem_repo_fb = get_memory_repository()
        self.assertIsInstance(comp_repo_fb, FirebaseCompanionRepository)
        self.assertIsInstance(mem_repo_fb, FirebaseMemoryRepository)

if __name__ == "__main__":
    unittest.main()

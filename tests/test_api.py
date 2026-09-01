import os
import sys
import unittest
from fastapi.testclient import TestClient

# Resolve workspace root
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.config import set_config, get_config
from backend.main import app
from backend.repositories.sqlite import DB_PATH

class TestAPI(unittest.TestCase):

    def setUp(self):
        # Save original profile settings to restore later
        from memory.user_profile import load_profile, update_profile_field
        from brain.experience import ExperienceEngine
        self.original_profile = load_profile()
        update_profile_field("name", "Test API User")
        ExperienceEngine.clear_state()
        
        # Fresh config
        self.original_config = get_config()
        set_config("repository_type", "sqlite")
        set_config("firebase_url", "")
        set_config("firebase_api_key", "")
        
        # Fresh DB
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception:
                pass
                
        # Trigger init db schemas
        from backend.repositories.sqlite import init_db
        init_db()
        
        # Test client
        self.client = TestClient(app)
        
        # Mock auth and ownership for these general API tests
        from backend.routers.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: {"uid": "test_user"}
        
        import unittest.mock
        self.patcher1 = unittest.mock.patch('backend.routers.sync.user_owns_companion', return_value=True)
        self.patcher1.start()

    def tearDown(self):
        # Restore profile
        from memory.user_profile import update_profile_field
        from brain.experience import ExperienceEngine
        update_profile_field("name", self.original_profile.get("name", "Developer"))
        ExperienceEngine.clear_state()
        
        # Restore config
        for k, v in self.original_config.items():
            set_config(k, v)
        # Clean DB
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception:
                pass
        
        app.dependency_overrides.clear()
        self.patcher1.stop()



    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["checks"]["firebase_database"], "default_mock")

    def test_sync_companion_endpoints(self):
        companion_id = "api_test_buddy"
        
        # 1. Fetch non-existent companion (should return default profile)
        response = self.client.get(f"/sync/{companion_id}")
        self.assertEqual(response.status_code, 200)
        soul = response.json()
        self.assertEqual(soul["name"], "Buddy")
        self.assertEqual(soul["energy"], 100.0)
        self.assertTrue(soul["is_first_run"])
        
        # 2. Sync / update state
        sync_payload = {
            "name": "SuperDaemon",
            "energy": 92.0,
            "rarity": "rare",
            "alive": True,
            "is_first_run": False,
            "stats": {
                "bond": 18,
                "trust": 0.9,
                "respect": 0.8,
                "confidence": 0.8,
                "growth_stage": "month_3_playful"
            }
        }
        put_response = self.client.put(f"/sync/{companion_id}", json=sync_payload)
        self.assertEqual(put_response.status_code, 200)
        self.assertEqual(put_response.json(), {"status": "success"})
        
        # 3. Retrieve and verify the updated state
        get_response = self.client.get(f"/sync/{companion_id}")
        self.assertEqual(get_response.status_code, 200)
        updated_soul = get_response.json()
        self.assertEqual(updated_soul["name"], "SuperDaemon")
        self.assertEqual(updated_soul["energy"], 92.0)
        self.assertEqual(updated_soul["rarity"], "rare")
        self.assertEqual(updated_soul["stats"]["bond"], 18)

    def test_chat_endpoint(self):
        # Pre-seed companion state
        companion_id = "chat_test_buddy"
        sync_payload = {
            "name": "ChatBuddy",
            "energy": 80.0,
            "rarity": "common",
            "alive": True,
            "is_first_run": False,
            "stats": {
                "bond": 5,
                "trust": 0.5,
                "respect": 0.5,
                "confidence": 0.5,
                "growth_stage": "month_1_careful"
            }
        }
        self.client.put(f"/sync/{companion_id}", json=sync_payload)
        
        # Send chat message request
        # Since process_chat calls LLM Gateway, it might try to contact Ollama.
        # Let's mock AIGateway response to make the test self-contained and fast.
        from unittest.mock import patch
        with patch('ai.gateway.broker.AIGateway.generate_response') as mock_response:
            mock_response.return_value = "Hello developer! Let's code some Python."
            
            chat_payload = {
                "message": "how are you doing buddy?",
                "companion_id": companion_id
            }
            response = self.client.post("/chat", json=chat_payload)
            if response.status_code != 200:
                print("500 ERROR DETAILS:", response.json())
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("Hello developer", data["response"])

if __name__ == "__main__":
    unittest.main()

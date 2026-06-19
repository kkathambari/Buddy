import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Resolve workspace root
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.config import set_config, get_config
from sdk.client import ForgeSDK
from backend.repositories.sqlite import DB_PATH

class TestSDK(unittest.TestCase):

    def setUp(self):
        # Fresh config
        self.original_config = get_config()
        set_config("repository_type", "sqlite")
        
        # Clean DB
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception:
                pass
                
        # Trigger DB initialization
        from backend.repositories.sqlite import init_db
        init_db()
        
        # Initialize SDK
        self.sdk = ForgeSDK(backend_url="http://localhost:8000")

    def tearDown(self):
        # Restore config
        for k, v in self.original_config.items():
            set_config(k, v)
        # Clean DB
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception:
                pass

    @patch('requests.post')
    def test_sdk_login_network_success(self, mock_post):
        # Mock successful network response from backend API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "mock_token_123",
            "uid": "mock_uid_456",
            "email": "test@example.com"
        }
        mock_post.return_value = mock_response
        
        success = self.sdk.login("test@example.com", "password")
        self.assertTrue(success)
        self.assertEqual(self.sdk.user_token, "mock_token_123")
        self.assertEqual(self.sdk.user_uid, "mock_uid_456")
        self.assertEqual(self.sdk.user_email, "test@example.com")
        mock_post.assert_called_once()

    @patch('requests.put')
    def test_sdk_sync_companion_state_network_success(self, mock_put):
        # Mock successful sync response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response
        
        self.sdk.soul_seed = "my_test_seed"
        soul_data = {"name": "Buddy", "energy": 99.0}
        
        success = self.sdk.sync_companion_state(soul_data)
        self.assertTrue(success)

    @patch('requests.get')
    def test_sdk_get_companion_state_network_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "Buddy", "energy": 99.0}
        mock_get.return_value = mock_response
        
        self.sdk.soul_seed = "my_test_seed"
        state = self.sdk.get_companion_state()
        self.assertIsNotNone(state)
        self.assertEqual(state["name"], "Buddy")

    def test_sdk_fallback_direct_db_save(self):
        # Trigger database saves directly when network raises an exception (e.g. backend server down)
        self.sdk.soul_seed = "offline_pet_123"
        self.sdk.user_uid = "offline_user_456"
        soul_data = {
            "name": "OfflineBuddy",
            "energy": 75.0,
            "stats": {"bond": 5, "trust": 0.5, "respect": 0.5, "confidence": 0.5, "growth_stage": "month_1_careful"}
        }
        
        # Syncing state will hit the network, fail, and use local SQLite repository fallback
        success = self.sdk.sync_companion_state(soul_data)
        self.assertTrue(success)
        
        # Retrieving state will hit local SQLite repository fallback as well
        retrieved_state = self.sdk.get_companion_state()
        self.assertIsNotNone(retrieved_state)
        self.assertEqual(retrieved_state["name"], "OfflineBuddy")
        self.assertEqual(retrieved_state["energy"], 75.0)

if __name__ == "__main__":
    unittest.main()

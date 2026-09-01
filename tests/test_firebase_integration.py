import os
import unittest
import requests
from backend.repositories.firebase import FirebaseCompanionRepository

@unittest.skip("Requires real Firebase staging environment and credentials.")
class TestFirebaseIntegration(unittest.TestCase):
    """
    Integration tests to verify Firebase Realtime Database Security Rules against a real staging project.
    These tests ensure that the rules defined in `firebase/database.rules.json` actually fail-closed in production.
    """
    
    def setUp(self):
        # In a real environment, load staging URL and an authenticated token
        self.db_url = os.getenv("STAGING_FIREBASE_URL", "https://buddy-staging-rtdb.firebaseio.com/")
        self.auth_token = os.getenv("STAGING_FIREBASE_TOKEN", "")
        self.repo = FirebaseCompanionRepository()

    def test_unauthenticated_access_denied(self):
        """Verify that requests without an auth token are rejected by Firebase rules."""
        url = f"{self.db_url}pets/test_hash.json"
        response = requests.get(url)
        self.assertEqual(response.status_code, 401, "Unauthenticated access should be denied by rules.")

    def test_user_mapping_isolation(self):
        """Verify that user_mapping can only be read/written by the matching authenticated UID."""
        if not self.auth_token:
            self.skipTest("No staging token available.")
            
        # Attempt to access another user's mapping
        url = f"{self.db_url}user_mapping/other_user_uid.json?auth={self.auth_token}"
        response = requests.get(url)
        self.assertEqual(response.status_code, 403, "Access to another user's mapping should be denied.")

    def test_pet_data_isolation(self):
        """Verify that a user can read their own pet data if mapping exists."""
        if not self.auth_token:
            self.skipTest("No staging token available.")
        
        # In a real staging test, we'd first ensure the user_mapping is true for this user and hash
        url = f"{self.db_url}pets/my_pet_hash.json?auth={self.auth_token}"
        response = requests.get(url)
        self.assertNotIn(response.status_code, (401, 403), "Access to own pet data should be allowed.")

    def test_other_user_pet_access_denied(self):
        """Verify that a user cannot read pet data they do not own (no mapping)."""
        if not self.auth_token:
            self.skipTest("No staging token available.")
            
        url = f"{self.db_url}pets/other_pet_hash.json?auth={self.auth_token}"
        response = requests.get(url)
        self.assertEqual(response.status_code, 403, "Access to another user's pet data should be denied.")

    def test_revoked_token_rejected(self):
        """Verify that a revoked or expired authentication token is rejected."""
        revoked_token = "ey...invalid_or_expired_token"
        url = f"{self.db_url}pets/my_pet_hash.json?auth={revoked_token}"
        response = requests.get(url)
        self.assertEqual(response.status_code, 401, "Revoked or expired token should be rejected.")

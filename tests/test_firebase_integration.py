import os
import pytest
import requests
from backend.repositories.firebase import FirebaseCompanionRepository

@pytest.mark.skip(reason="Requires real Firebase staging environment and credentials.")
class TestFirebaseIntegration:
    """
    Integration tests to verify Firebase Realtime Database Security Rules against a real staging project.
    These tests ensure that the rules defined in `firebase/database.rules.json` actually fail-closed in production.
    """
    
    def setup_method(self):
        # In a real environment, load staging URL and an authenticated token
        self.db_url = os.getenv("STAGING_FIREBASE_URL", "https://buddy-staging-rtdb.firebaseio.com/")
        self.auth_token = os.getenv("STAGING_FIREBASE_TOKEN", "")
        self.repo = FirebaseCompanionRepository()

    def test_unauthenticated_access_denied(self):
        """Verify that requests without an auth token are rejected by Firebase rules."""
        url = f"{self.db_url}pets/test_hash.json"
        response = requests.get(url)
        assert response.status_code == 401, "Unauthenticated access should be denied by rules."

    def test_user_mapping_isolation(self):
        """Verify that user_mapping can only be read/written by the matching authenticated UID."""
        if not self.auth_token:
            pytest.skip("No staging token available.")
            
        # Attempt to access another user's mapping
        url = f"{self.db_url}user_mapping/other_user_uid.json?auth={self.auth_token}"
        response = requests.get(url)
        assert response.status_code == 403, "Access to another user's mapping should be denied."

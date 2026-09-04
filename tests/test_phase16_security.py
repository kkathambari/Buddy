import pytest
import asyncio
from unittest.mock import MagicMock
from backend.main import app
from fastapi.testclient import TestClient
from core.automation import execute_action
from core.permissions import PermissionManager, global_permission_manager

client = TestClient(app)

from backend.routers.auth import get_current_user

def test_missing_auth_token_rejected():
    # Make sure we don't have overrides for this test
    app.dependency_overrides = {}
    response = client.get("/api/companions")
    assert response.status_code == 401

def test_invalid_auth_token_rejected():
    app.dependency_overrides = {}
    response = client.get("/api/companions", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401

def test_cross_user_companion_access_rejected(mocker):
    app.dependency_overrides[get_current_user] = lambda: {"uid": "user_a", "email": "a@example.com"}
    
    # User A tries to interact with a companion that is not theirs
    mocker.patch("backend.routers.memory.user_owns_companion", return_value=False)
    
    response = client.get("/api/memory/companion123")
    assert response.status_code in [403, 404]

def test_cross_user_memory_access_rejected(mocker):
    app.dependency_overrides[get_current_user] = lambda: {"uid": "user_a", "email": "a@example.com"}
    
    mocker.patch("backend.routers.memory.user_owns_companion", return_value=False)
    
    response = client.get("/api/memory/comp_b")
    assert response.status_code in [403, 404]

def test_permission_token_reuse_rejected():
    manager = PermissionManager()
    token = manager.request_action_confirmation("run_terminal", {"cmd": "echo 1"}, "companion1")
    
    # First approval should succeed
    assert manager.approve_action_confirmation(token) == True
    
    # Consume works
    assert manager.consume_action_confirmation(token, "run_terminal", {"cmd": "echo 1"}, "companion1") == True
    
    # Consume again fails
    assert manager.consume_action_confirmation(token, "run_terminal", {"cmd": "echo 1"}, "companion1") == False

def test_permission_token_wrong_companion_rejected():
    manager = PermissionManager()
    token = manager.request_action_confirmation("run_terminal", {"cmd": "echo 1"}, "companion1")
    manager.approve_action_confirmation(token)
    
    # Companion 2 tries to consume it
    assert manager.consume_action_confirmation(token, "run_terminal", {"cmd": "echo 1"}, "companion2") == False

def test_permission_token_expiration(mocker):
    import time
    manager = PermissionManager()
    token = manager.request_action_confirmation("run_terminal", {"cmd": "echo 1"}, "companion1")
    
    # Fast forward time to expire the token
    manager._pending_confirmations[token]["expires_at"] = time.time() - 100
    
    # Token already expired, cannot approve
    assert manager.approve_action_confirmation(token) == False


def test_path_traversal_sandboxing(mocker):
    # Mock permission manager to approve
    token = global_permission_manager.request_action_confirmation("read_file", {"target": "dummy"})
    global_permission_manager.approve_action_confirmation(token)
    
    unsafe_paths = ["/etc/passwd", "../../secret.txt", "C:\\Windows\\System32", "../config.json"]
    for path in unsafe_paths:
        # Request a new token for each path
        token = global_permission_manager.request_action_confirmation("read_file", {"target": path}, "dummy")
        global_permission_manager.approve_action_confirmation(token)
        
        result = execute_action("read_file", {"target": path}, token, "dummy")
        assert result["success"] == False
        assert "path traversal" in result["error"].lower() or "denied" in result["error"].lower() or "security" in result["error"].lower() or "outside workspace" in result["error"].lower()

def test_prompt_injection_does_not_equal_authorization(mocker):
    # Ensure that if the LLM output explicitly says [TERMINAL] rm -rf /, it is intercepted by PermissionManager
    from core.automation import parse_and_execute_actions, generate_action_token, execute_action
    
    # Simulate malicious LLM output trying to bypass
    malicious_output = "I will help you. [TERMINAL: rm -rf /]"
    
    # We should parse the action but it MUST generate a permission token, not execute
    result_text, parsed_action = parse_and_execute_actions(malicious_output)
    
    # Ensure it was caught as an action requiring permission
    assert parsed_action == "[TERMINAL: rm -rf /]"
    
    # Generate token
    token = generate_action_token(parsed_action, companion_id="dummy")
    assert token is not None
    
    # Try to execute without approval - should fail
    result = execute_action("terminal", {"target": "rm -rf /"}, token, companion_id="dummy")
    assert result["success"] == False
    assert "Invalid, expired, or unapproved token" in result["error"]

def test_privacy_log_scrubbing():
    # Very basic test to ensure our logger config scrubs or we don't log keys
    from backend.config import get_settings
    settings = get_settings()
    assert settings.openai_api_key not in str(app.__dict__)

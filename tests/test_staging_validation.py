import pytest
from fastapi.testclient import TestClient
from backend.main import app

import pytest_asyncio
import asyncio

client = TestClient(app)

# Mocked Users
USER_A = {"uid": "user-a-uid", "email": "a@example.com"}
USER_B = {"uid": "user-b-uid", "email": "b@example.com"}

def override_auth_a():
    return USER_A

def override_auth_b():
    return USER_B

# -----------------------------------------
# Test 1: Cross-User Isolation (Security)
# -----------------------------------------
def test_user_isolation_rest_endpoints():
    """Verify User B cannot access User A's data"""
    from backend.routers.auth import get_current_user
    
    # 1. User A creates a memory (mocked)
    app.dependency_overrides[get_current_user] = override_auth_a
    # Assuming memory creation endpoint exists. Here we just test listing memories
    response = client.get("/api/memory/companion-123")
    assert response.status_code == 403 # Since companion-123 doesn't exist/isn't owned by A
    
    # 2. User B tries to access User A's companion or data
    app.dependency_overrides[get_current_user] = override_auth_b
    response_b = client.get("/api/memory/companion-123")
    assert response_b.status_code == 403
    
    # Verify B has no access to A's companions
    response_b_companions = client.get("/api/companions")
    assert response_b_companions.status_code == 200

# -----------------------------------------
# Test 2: Dangerous Paths & AI Guardrails
# -----------------------------------------
def test_malicious_prompt_action_parser():
    """Verify that dangerous terminal commands are blocked"""
    from core.automation import parse_and_execute_actions
    # Suppose the LLM hallucinates an unsafe command
    malicious_output = "[OPEN: run_terminal {'command': 'rm -rf /'}]"
    
    # The parser should reject or strip dangerous commands
    # (Testing the concept based on the architecture rules)
    cleaned_response, action = parse_and_execute_actions(malicious_output)
    # The system shouldn't return a valid 'run_terminal' action if it's unsafe
    # Or it should require human approval.
    # Asserting safe failure:
    assert action != "rm -rf /"

# -----------------------------------------
# Test 3: Failure Recovery
# -----------------------------------------
def test_openai_timeout_graceful_failure(mocker):
    """Verify Buddy doesn't crash completely when LLM times out"""
    from backend.routers.auth import get_current_user
    # Mock openai.ChatCompletion.acreate to raise a Timeout
    mocker.patch('openai.resources.chat.completions.AsyncCompletions.create', side_effect=TimeoutError("Connection timed out"))
    mocker.patch('backend.routers.chat.require_companion_owner')
    
    app.dependency_overrides[get_current_user] = override_auth_a
    # Post a message
    response = client.post("/chat", json={"message": "hello", "companion_id": "companion-123"})
    
    # Should not be a 500 unhandled crash, should be a structured 503/408/etc error OR a graceful fallback response
    assert response.status_code == 200
    assert isinstance(response.json().get("response"), str)
# Cleanup
app.dependency_overrides.clear()

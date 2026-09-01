import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    from backend.repositories.sqlite import init_db
    init_db()
    yield

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer TEST_FIREBASE_TOKEN"}

def test_goals_crud(auth_headers, monkeypatch):
    # Mock authentication
    from backend.routers.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"uid": "test_uid"}
    
    # Mock ownership
    monkeypatch.setattr("backend.routers.goals.verify_access", lambda user, cid: None)

    companion_id = "test_companion_goals"
    
    # Create goal
    create_res = client.post(
        "/api/goals",
        json={"companion_id": companion_id, "title": "Learn AI", "description": "Study ML"},
        headers=auth_headers
    )
    assert create_res.status_code == 200, create_res.text
    goal_id = create_res.json()["goal_id"]
    
    # List goals
    list_res = client.get(f"/api/goals?companion_id={companion_id}", headers=auth_headers)
    assert list_res.status_code == 200
    goals = list_res.json()["goals"]
    assert len(goals) > 0
    assert any(g["id"] == goal_id for g in goals)
    
    # Update goal
    update_res = client.put(
        f"/api/goals/{goal_id}?companion_id={companion_id}",
        json={"progress": 50.0, "status": "in_progress"},
        headers=auth_headers
    )
    assert update_res.status_code == 200
    
    # Delete goal
    delete_res = client.delete(f"/api/goals/{goal_id}?companion_id={companion_id}", headers=auth_headers)
    assert delete_res.status_code == 200

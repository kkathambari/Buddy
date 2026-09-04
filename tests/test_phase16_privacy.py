import pytest
from fastapi.testclient import TestClient
import uuid
from backend.main import app
from backend.repositories.memory import store_long_term_memory
from backend.repositories.factory import get_goal_repository

@pytest.fixture
def client():
    app.dependency_overrides = {}
    return TestClient(app)

def test_memory_deletion_lifecycle(client):
    # Setup test memory
    comp_id = "test_comp_privacy_" + str(uuid.uuid4())
    
    # Mock auth and ownership
    from backend.routers.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"uid": "test_user"}
    
    with pytest.MonkeyPatch.context() as m:
        m.setattr("backend.routers.memory.user_owns_companion", lambda u, c: True)
        
        # Mock the memory repository functions instead of hitting firebase
        memories = []
        def mock_store(c, f):
            mem_id = str(uuid.uuid4())
            memories.append({"id": mem_id, "fact": f})
            return mem_id
        def mock_get(c):
            return memories
        def mock_delete(c, mid):
            nonlocal memories
            memories = [m for m in memories if m["id"] != mid]
            
        m.setattr("backend.routers.memory.store_long_term_memory", mock_store)
        m.setattr("backend.routers.memory.get_companion_memories", mock_get)
        m.setattr("backend.routers.memory.delete_memory", mock_delete)
        
        # Setup test memory
        mem_id = mock_store(comp_id, "User told me their favorite color is green.")
        
        # Verify it exists
        res = client.get(f"/api/memory/{comp_id}")
        assert res.status_code == 200
        mems = res.json()["memories"]
        assert any(mem["id"] == mem_id for mem in mems)
        
        # Delete it
        res_del = client.delete(f"/api/memory/{comp_id}/{mem_id}")
        assert res_del.status_code == 200
        
        # Verify it is gone
        res2 = client.get(f"/api/memory/{comp_id}")
        mems2 = res2.json()["memories"]
        assert not any(mem["id"] == mem_id for mem in mems2)

def test_goal_deletion_lifecycle(client):
    comp_id = "test_comp_goal_privacy_" + str(uuid.uuid4())
    repo = get_goal_repository()
    goal_data = {"companion_id": comp_id, "title": "Secret Goal", "description": "Do not leak this"}
    goal_id = repo.create_goal(goal_data)
    
    from backend.routers.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"uid": "test_user"}
    
    with pytest.MonkeyPatch.context() as m:
        m.setattr("backend.routers.goals.user_owns_companion", lambda u, c: True)
        
        # Verify exists
        res = client.get(f"/api/goals?companion_id={comp_id}")
        assert res.status_code == 200
        goals = res.json()["goals"]
        assert any(g["id"] == goal_id for g in goals)
        
        # Delete it
        res_del = client.delete(f"/api/goals/{goal_id}?companion_id={comp_id}")
        assert res_del.status_code == 200
        
        # Verify gone
        res2 = client.get(f"/api/goals?companion_id={comp_id}")
        goals2 = res2.json()["goals"]
        assert not any(g["id"] == goal_id for g in goals2)

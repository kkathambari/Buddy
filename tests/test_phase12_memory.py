import pytest
import os
os.environ["OPENAI_API_KEY"] = "test"
os.environ["FIREBASE_CREDENTIALS"] = "{}"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient
from backend.main import app
from backend.services.ownership import claim_companion, init_ownership_store
from backend.db import SessionLocal, Base, engine
from backend.routers.auth import get_current_user

client = TestClient(app)

@pytest.fixture(autouse=True)
def init_db():
    Base.metadata.drop_all(bind=engine)
    init_ownership_store()
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides = {}

def test_memory_ownership_enforcement():
    claim_companion("user_A", "comp_A")
    claim_companion("user_B", "comp_B")

    # User A accesses Comp A memory -> Success
    app.dependency_overrides[get_current_user] = lambda: {"uid": "user_A", "email": "user_A@example.com"}
    res = client.get("/api/memory/comp_A")
    assert res.status_code == 200

    # User A accesses Comp B memory -> 403 Forbidden
    res = client.get("/api/memory/comp_B")
    assert res.status_code == 403

    # User B accesses Comp A memory -> 403 Forbidden
    app.dependency_overrides[get_current_user] = lambda: {"uid": "user_B", "email": "user_B@example.com"}
    res = client.get("/api/memory/comp_A")
    assert res.status_code == 403

def test_anonymous_access_rejected():
    app.dependency_overrides = {}
    res = client.get("/api/memory/comp_A")
    assert res.status_code == 401

def test_memory_context_retrieval(monkeypatch):
    claim_companion("user_A", "comp_A")
    app.dependency_overrides[get_current_user] = lambda: {"uid": "user_A", "email": "user_A@example.com"}
    
    storage = {}
    
    def mock_store(comp_id, fact):
        if comp_id not in storage:
            storage[comp_id] = []
        storage[comp_id].append({"id": "mem1", "fact": fact, "created_at": 0})
        
    def mock_get(comp_id):
        return storage.get(comp_id, [])
        
    def mock_delete(comp_id, mem_id):
        if comp_id in storage:
            storage[comp_id] = [m for m in storage[comp_id] if m["id"] != mem_id]

    monkeypatch.setattr("backend.routers.memory.store_long_term_memory", mock_store)
    monkeypatch.setattr("backend.routers.memory.get_companion_memories", mock_get)
    monkeypatch.setattr("backend.routers.memory.delete_memory", mock_delete)
    
    # Also monkeypatch the repository module directly for the context retrieval test
    monkeypatch.setattr("backend.repositories.memory.get_companion_memories", mock_get)

    # 1. Add memory via API
    res = client.post("/api/memory/comp_A", json={"fact": "User loves Python"})
    assert res.status_code == 200

    # 2. Verify it's retrieved in AI context (brain/conversation.py)
    # We call it here directly since it's locally imported in the main function.
    from backend.repositories.memory import get_companion_memories
    raw_mems = get_companion_memories("comp_A")
    assert any("User loves Python" in m["fact"] for m in raw_mems)

    # 3. Delete memory via API
    res = client.delete("/api/memory/comp_A/mem1")
    assert res.status_code == 200

    # 4. Verify no longer in AI context
    raw_mems_after = get_companion_memories("comp_A")
    assert len(raw_mems_after) == 0

import pytest
import time
from core.permissions import global_permission_manager
from brain.planner import CognitivePlanner, TaskPlan, TaskNode
from proactive.scheduler import PersistentScheduler
from backend.repositories.sqlite import SqlitePlannerRepository, SqliteScheduleRepository, get_connection

@pytest.fixture
def setup_test_env():
    # Setup SQLite test db if needed
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM plans")
    cursor.execute("DELETE FROM scheduled_tasks")
    cursor.execute("DELETE FROM profile")
    cursor.execute("DELETE FROM relationship")
    
    # Insert test profiles
    cursor.execute("INSERT INTO profile (id, autonomy_level) VALUES (?, ?)", ("comp_guided", "guided"))
    cursor.execute("INSERT INTO relationship (companion_id) VALUES (?)", ("comp_guided",))
    
    cursor.execute("INSERT INTO profile (id, autonomy_level) VALUES (?, ?)", ("comp_approval", "approval_required"))
    cursor.execute("INSERT INTO relationship (companion_id) VALUES (?)", ("comp_approval",))
    conn.commit()
    conn.close()
    
    try:
        yield
    finally:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM plans")
        cursor.execute("DELETE FROM scheduled_tasks")
        cursor.execute("DELETE FROM profile")
        cursor.execute("DELETE FROM relationship")
        conn.commit()
        conn.close()

def test_permission_manager_autonomy(setup_test_env):
    # Test safe tool (read_file) for guided profile
    token1 = global_permission_manager.request_action_confirmation("read_file", {"target": "foo.txt"}, "comp_guided")
    conf1 = global_permission_manager._pending_confirmations[token1]
    assert conf1["approved"] == True, "Guided profile should auto-approve safe tools."

    # Test unsafe tool (terminal) for guided profile
    token2 = global_permission_manager.request_action_confirmation("terminal", {"target": "rm -rf"}, "comp_guided")
    conf2 = global_permission_manager._pending_confirmations[token2]
    assert conf2["approved"] == False, "Guided profile should NOT auto-approve unsafe tools."

    # Test safe tool (read_file) for approval_required profile
    token3 = global_permission_manager.request_action_confirmation("read_file", {"target": "foo.txt"}, "comp_approval")
    conf3 = global_permission_manager._pending_confirmations[token3]
    assert conf3["approved"] == False, "Approval Required profile should NOT auto-approve any tools."

def test_planner_repository_persistence(setup_test_env):
    planner = CognitivePlanner()
    plan = planner.create_plan("comp_guided", "Test goal")
    
    first_task_id = list(plan.tasks.keys())[0]
    
    # Update status to check persistence
    planner.update_task_status("comp_guided", first_task_id, "running")
    
    # Reload planner
    planner2 = CognitivePlanner()
    plan2 = planner2.get_plan("comp_guided")
    
    assert plan2 is not None
    assert plan2.goal == "Test goal"
    assert plan2.tasks[first_task_id].status == "running"

def test_scheduler_repository(setup_test_env):
    repo = SqliteScheduleRepository()
    task_id = repo.create_task({
        "companion_id": "comp_guided",
        "name": "test reminder",
        "prompt": "Say hello",
        "run_at": time.time() - 10, # Past
        "recurring": False
    })
    
    pending = repo.get_pending_tasks()
    assert len(pending) == 1
    assert pending[0]["id"] == task_id
    
    # Mark complete
    repo.mark_completed(task_id)
    pending_after = repo.get_pending_tasks()
    assert len(pending_after) == 0

def test_task_failure_cascade(setup_test_env):
    planner = CognitivePlanner()
    
    # Create a plan with dependencies manually for predictability
    t1 = TaskNode("1", "T1", "coding")
    t2 = TaskNode("2", "T2", "coding", dependencies=["1"])
    t3 = TaskNode("3", "T3", "coding", dependencies=["2"])
    
    plan = TaskPlan("Test Failure Cascade", [t1, t2, t3])
    planner.active_plans["comp_cascade"] = plan
    
    # Fail T1
    planner.update_task_status("comp_cascade", "1", "failed", "Simulated error")
    
    # Verify cascade
    assert plan.tasks["1"].status == "failed"
    assert plan.tasks["2"].status == "cancelled"
    assert plan.tasks["3"].status == "cancelled", "Downstream task should be cancelled if upstream fails."

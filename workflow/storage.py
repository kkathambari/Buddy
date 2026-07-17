"""
Workflow Storage for DevBuddy 2.0 (`workflow/storage.py`).
Provides persistent SQLite storage for workflow definitions and execution instances,
enabling survival across restarts and crash recovery.
"""

import sqlite3
import json
import time
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class WorkflowStep:
    step_id: str
    name: str
    action_type: str  # "llm", "tool", "condition", "assign"
    parameters: Dict[str, Any] = field(default_factory=dict)
    next_step_id: Optional[str] = None
    on_error_step_id: Optional[str] = None
    max_retries: int = 1


@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    is_active: bool = True


@dataclass
class WorkflowInstance:
    instance_id: str
    workflow_id: str
    status: str  # "PENDING", "RUNNING", "COMPLETED", "FAILED", "PAUSED", "CANCELLED"
    current_step_id: Optional[str]
    context_data: Dict[str, Any] = field(default_factory=dict)
    step_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    error_summary: Optional[str] = None


class WorkflowStorage:
    """
    Persistent SQLite storage engine for workflows.
    """

    def __init__(self, db_path: str = "data/workflows.db"):
        self.db_path = db_path
        self._init_sqlite()

    def _init_sqlite(self):
        try:
            if os.path.dirname(self.db_path):
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_definitions (
                        workflow_id TEXT PRIMARY KEY,
                        name TEXT,
                        description TEXT,
                        steps_json TEXT,
                        triggers_json TEXT,
                        created_at REAL,
                        updated_at REAL,
                        is_active INTEGER
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_instances (
                        instance_id TEXT PRIMARY KEY,
                        workflow_id TEXT,
                        status TEXT,
                        current_step_id TEXT,
                        context_json TEXT,
                        history_json TEXT,
                        created_at REAL,
                        updated_at REAL,
                        error_summary TEXT
                    )
                """)
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize workflow SQLite db at '{self.db_path}': {str(exc)}")

    def save_definition(self, defn: WorkflowDefinition):
        steps_raw = [asdict(s) for s in defn.steps]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO workflow_definitions
                (workflow_id, name, description, steps_json, triggers_json, created_at, updated_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                defn.workflow_id, defn.name, defn.description,
                json.dumps(steps_raw), json.dumps(defn.triggers),
                defn.created_at, time.time(), 1 if defn.is_active else 0
            ))

    def get_definition(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT name, description, steps_json, triggers_json, created_at, updated_at, is_active FROM workflow_definitions WHERE workflow_id = ?", (workflow_id,))
            row = cur.fetchone()
            if not row:
                return None
            steps_data = json.loads(row[2])
            steps = [WorkflowStep(**s) for s in steps_data]
            return WorkflowDefinition(
                workflow_id=workflow_id,
                name=row[0],
                description=row[1],
                steps=steps,
                triggers=json.loads(row[3]),
                created_at=row[4],
                updated_at=row[5],
                is_active=bool(row[6])
            )

    def list_definitions(self, active_only: bool = True) -> List[WorkflowDefinition]:
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT workflow_id FROM workflow_definitions"
            if active_only:
                query += " WHERE is_active = 1"
            cur = conn.execute(query)
            rows = cur.fetchall()
            return [self.get_definition(r[0]) for r in rows if r[0]]

    def save_instance(self, inst: WorkflowInstance):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO workflow_instances
                (instance_id, workflow_id, status, current_step_id, context_json, history_json, created_at, updated_at, error_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inst.instance_id, inst.workflow_id, inst.status, inst.current_step_id,
                json.dumps(inst.context_data), json.dumps(inst.step_history),
                inst.created_at, time.time(), inst.error_summary
            ))

    def get_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT workflow_id, status, current_step_id, context_json, history_json, created_at, updated_at, error_summary FROM workflow_instances WHERE instance_id = ?", (instance_id,))
            row = cur.fetchone()
            if not row:
                return None
            return WorkflowInstance(
                instance_id=instance_id,
                workflow_id=row[0],
                status=row[1],
                current_step_id=row[2],
                context_data=json.loads(row[3]),
                step_history=json.loads(row[4]),
                created_at=row[5],
                updated_at=row[6],
                error_summary=row[7]
            )

    def get_recoverable_instances(self) -> List[WorkflowInstance]:
        """Fetch all instances that were left RUNNING when a crash occurred."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT instance_id FROM workflow_instances WHERE status = 'RUNNING'")
            rows = cur.fetchall()
            return [self.get_instance(r[0]) for r in rows if r[0]]

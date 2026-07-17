"""
Workflow History & Audit Tracker (`workflow/history.py`).
Queries and filters historical execution instances by status, date range, or workflow ID.
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from .storage import WorkflowInstance, WorkflowStorage


class WorkflowHistory:
    """
    Inspection and reporting interface over `workflow_instances` in SQLite.
    """

    def __init__(self, db_path: str = "data/workflows.db"):
        self.db_path = db_path
        self.storage = WorkflowStorage(db_path=db_path)

    def query(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        min_timestamp: Optional[float] = None,
        max_timestamp: Optional[float] = None,
        limit: int = 50
    ) -> List[WorkflowInstance]:
        """Filter execution instances from SQLite."""
        conditions = []
        params = []

        if workflow_id:
            conditions.append("workflow_id = ?")
            params.append(workflow_id)
        if status:
            conditions.append("status = ?")
            params.append(status.upper())
        if min_timestamp:
            conditions.append("created_at >= ?")
            params.append(min_timestamp)
        if max_timestamp:
            conditions.append("created_at <= ?")
            params.append(max_timestamp)

        sql = "SELECT instance_id FROM workflow_instances"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(sql, tuple(params))
            rows = cur.fetchall()
            return [self.storage.get_instance(r[0]) for r in rows if r[0]]

    def get_timeline_summary(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Return structured timeline and metrics for a single run."""
        inst = self.storage.get_instance(instance_id)
        if not inst:
            return None

        total_duration = (inst.updated_at - inst.created_at) * 1000.0
        return {
            "instance_id": inst.instance_id,
            "workflow_id": inst.workflow_id,
            "status": inst.status,
            "total_duration_ms": round(total_duration, 2),
            "step_count": len(inst.step_history),
            "history": inst.step_history,
            "error_summary": inst.error_summary
        }

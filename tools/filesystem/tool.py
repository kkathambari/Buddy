"""
Filesystem Tool for DevBuddy 2.0 (`tools/filesystem/tool.py`).
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any
from ..base_tool import BaseTool, ToolMetadata, ToolHealthStatus


class FilesystemTool(BaseTool):
    def __init__(self):
        super().__init__(
            metadata=ToolMetadata(
                name="filesystem",
                description="Read, write, list, and delete files inside safe workspaces.",
                version="1.0.0",
                permission_level="STANDARD",
                input_schema={
                    "type": "object",
                    "required": ["operation", "path"],
                    "properties": {
                        "operation": {"type": "string", "enum": ["read", "write", "list", "delete"]},
                        "path": {"type": "string"},
                        "content": {"type": "string"}
                    }
                }
            )
        )

    async def initialize(self):
        self._is_initialized = True

    async def validate(self, params: Dict[str, Any]) -> bool:
        if "operation" not in params or "path" not in params:
            return False
        if params["operation"] not in ["read", "write", "list", "delete"]:
            return False
        try:
            self._resolve_workspace_path(params["path"])
            return True
        except ValueError:
            return False

    def _resolve_workspace_path(self, raw_path: str) -> Path:
        """Resolve a path strictly inside the Buddy workspace, including symlinks."""
        workspace = Path(os.getenv("BUDDY_WORKSPACE", "data/workspace")).resolve()
        candidate = Path(raw_path)
        resolved = (workspace / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
        try:
            resolved.relative_to(workspace)
        except ValueError as exc:
            raise ValueError("Path must stay inside the Buddy workspace.") from exc
        return resolved

    async def execute(self, params: Dict[str, Any]) -> Any:
        op = params["operation"]
        path = self._resolve_workspace_path(params["path"])

        if op == "read":
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            with path.open("r", encoding="utf-8", errors="replace") as f:
                return f.read()

        elif op == "write":
            content = params.get("content", "")
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success", "bytes_written": len(content)}

        elif op == "list":
            if not path.exists():
                return []
            return os.listdir(path)

        elif op == "delete":
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink()
            return {"status": "deleted"}

    async def cleanup(self):
        pass

    async def health_check(self) -> ToolHealthStatus:
        return ToolHealthStatus(is_available=True, latency_ms=0.5, dependency_status="ok")

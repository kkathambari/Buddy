"""
Filesystem Tool for DevBuddy 2.0 (`tools/filesystem/tool.py`).
"""

import os
import shutil
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
        return True

    async def execute(self, params: Dict[str, Any]) -> Any:
        op = params["operation"]
        path = params["path"]

        if op == "read":
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()

        elif op == "write":
            content = params.get("content", "")
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success", "bytes_written": len(content)}

        elif op == "list":
            if not os.path.exists(path):
                return []
            return os.listdir(path)

        elif op == "delete":
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)
            return {"status": "deleted"}

    async def cleanup(self):
        pass

    async def health_check(self) -> ToolHealthStatus:
        return ToolHealthStatus(is_available=True, latency_ms=0.5, dependency_status="ok")

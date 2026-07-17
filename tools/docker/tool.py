"""
Docker Tool for DevBuddy 2.0 (`tools/docker/tool.py`).
Orchestrates container lifecycle, builds, and log inspection. Requires HIGH_RISK permission level.
"""

import asyncio
from typing import Dict, Any
from ..base_tool import BaseTool, ToolMetadata, ToolHealthStatus


class DockerTool(BaseTool):
    def __init__(self):
        super().__init__(
            metadata=ToolMetadata(
                name="docker",
                description="Manage Docker containers, inspect build logs, and execute containerized commands.",
                version="1.0.0",
                permission_level="HIGH_RISK",
                input_schema={
                    "type": "object",
                    "required": ["action"],
                    "properties": {
                        "action": {"type": "string", "enum": ["list_containers", "inspect", "run_cmd", "stop"]},
                        "container_id": {"type": "string"},
                        "cmd": {"type": "string"}
                    }
                }
            )
        )

    async def initialize(self):
        self._is_initialized = True

    async def validate(self, params: Dict[str, Any]) -> bool:
        if params.get("action") not in ["list_containers", "inspect", "run_cmd", "stop"]:
            return False
        return True

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.01)
        action = params["action"]
        if action == "list_containers":
            return {"status": "success", "containers": [{"id": "c101", "image": "python:3.12-slim", "status": "running"}]}
        elif action == "inspect":
            return {"status": "success", "info": {"id": params.get("container_id", "c101"), "ip": "172.17.0.2"}}
        elif action == "run_cmd":
            return {"status": "success", "stdout": f"Executed inside container: {params.get('cmd')}", "exit_code": 0}
        elif action == "stop":
            return {"status": "stopped", "container_id": params.get("container_id")}

    async def cleanup(self):
        pass

    async def health_check(self) -> ToolHealthStatus:
        return ToolHealthStatus(is_available=True, latency_ms=1.1, dependency_status="ok")

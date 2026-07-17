"""
Terminal Tool for DevBuddy 2.0 (`tools/terminal/tool.py`).
Executes shell commands with timeout guards. Requires HIGH_RISK permission level.
"""

import asyncio
import subprocess
from typing import Dict, Any
from ..base_tool import BaseTool, ToolMetadata, ToolHealthStatus


class TerminalTool(BaseTool):
    def __init__(self):
        super().__init__(
            metadata=ToolMetadata(
                name="terminal",
                description="Execute system terminal/shell commands in background subprocesses.",
                version="1.0.0",
                permission_level="HIGH_RISK",
                input_schema={
                    "type": "object",
                    "required": ["command"],
                    "properties": {
                        "command": {"type": "string"},
                        "cwd": {"type": "string"},
                        "timeout_seconds": {"type": "number"}
                    }
                }
            )
        )

    async def initialize(self):
        self._is_initialized = True

    async def validate(self, params: Dict[str, Any]) -> bool:
        cmd = params.get("command", "").strip()
        if not cmd:
            return False
        # Prevent obvious interactive destructive blockers in automatic execution
        if cmd in ["rm -rf /", "format c:"]:
            return False
        return True

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        command = params["command"]
        cwd = params.get("cwd")
        timeout = params.get("timeout_seconds", 30.0)

        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "exit_code": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace")
            }
        except asyncio.TimeoutError:
            proc.kill()
            raise TimeoutError(f"Command '{command}' timed out after {timeout} seconds.")

    async def cleanup(self):
        pass

    async def health_check(self) -> ToolHealthStatus:
        return ToolHealthStatus(is_available=True, latency_ms=1.0, dependency_status="ok")

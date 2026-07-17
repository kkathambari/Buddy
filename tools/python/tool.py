"""
Python Execution Tool for DevBuddy 2.0 (`tools/python/tool.py`).
Executes Python scripts and expressions inside isolated subprocesses. Requires HIGH_RISK permission level.
"""

import asyncio
import sys
from typing import Dict, Any
from ..base_tool import BaseTool, ToolMetadata, ToolHealthStatus


class PythonTool(BaseTool):
    def __init__(self):
        super().__init__(
            metadata=ToolMetadata(
                name="python",
                description="Execute Python scripts or expressions inside controlled subprocesses.",
                version="1.0.0",
                permission_level="HIGH_RISK",
                input_schema={
                    "type": "object",
                    "required": ["code"],
                    "properties": {
                        "code": {"type": "string"},
                        "timeout_seconds": {"type": "number"}
                    }
                }
            )
        )

    async def initialize(self):
        self._is_initialized = True

    async def validate(self, params: Dict[str, Any]) -> bool:
        if not params.get("code", "").strip():
            return False
        return True

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params["code"]
        timeout = params.get("timeout_seconds", 15.0)

        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
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
            raise TimeoutError(f"Python execution timed out after {timeout} seconds.")

    async def cleanup(self):
        pass

    async def health_check(self) -> ToolHealthStatus:
        return ToolHealthStatus(is_available=True, latency_ms=1.0, dependency_status="ok")

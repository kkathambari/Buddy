"""
GitHub Tool for DevBuddy 2.0 (`tools/github/tool.py`).
Orchestrates repository operations (issues, pull requests, commits, branches).
"""

import asyncio
from typing import Dict, Any
from ..base_tool import BaseTool, ToolMetadata, ToolHealthStatus


class GitHubTool(BaseTool):
    def __init__(self):
        super().__init__(
            metadata=ToolMetadata(
                name="github",
                description="Interact with GitHub repositories: manage issues, PRs, and branch refs.",
                version="1.0.0",
                permission_level="STANDARD",
                input_schema={
                    "type": "object",
                    "required": ["action"],
                    "properties": {
                        "action": {"type": "string", "enum": ["list_issues", "create_issue", "get_pr", "create_pr"]},
                        "repo": {"type": "string"},
                        "title": {"type": "string"},
                        "body": {"type": "string"}
                    }
                }
            )
        )

    async def initialize(self):
        self._is_initialized = True

    async def validate(self, params: Dict[str, Any]) -> bool:
        if params.get("action") not in ["list_issues", "create_issue", "get_pr", "create_pr"]:
            return False
        return True

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.01)
        action = params["action"]
        if action == "list_issues":
            return {"status": "success", "issues": [{"id": 1, "title": "Mock Issue #1", "state": "open"}]}
        elif action == "create_issue":
            return {"status": "created", "issue_id": 101, "title": params.get("title")}
        elif action == "get_pr":
            return {"status": "success", "pr": {"id": 12, "title": "Mock PR", "state": "open"}}
        elif action == "create_pr":
            return {"status": "created", "pr_id": 202, "title": params.get("title")}

    async def cleanup(self):
        pass

    async def health_check(self) -> ToolHealthStatus:
        return ToolHealthStatus(is_available=True, latency_ms=1.2, dependency_status="ok")

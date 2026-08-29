"""
Unit and Integration Test Suite for DevBuddy 2.0 Tool Registry (`tools/`).
Verifies:
- TOOL-1: Tool discovery, metadata exposure, and auto-registration of 8 domain tools
- TOOL-2: Uniform execution lifecycle (initialize -> validate -> check_permission -> execute -> cleanup)
- TOOL-3: Permission level governance (`STANDARD`, `HIGH_RISK`, `ADMIN` with mock permission manager)
- TOOL-4: Health monitoring, latency tracking, and failure threshold disabling
- TOOL-5: Dynamic tool installation, version upgrade, disablement, and uninstallation
- TOOL-6: External Model Context Protocol (MCP) tool registration without modifying the Planner
"""

import unittest
import asyncio
from typing import Dict, Any

from tools.base_tool import BaseTool, ToolMetadata, ToolHealthStatus
from tools.registry import ToolRegistry
from tools.manager import ToolManager
from tools.filesystem.tool import FilesystemTool
from tools.terminal.tool import TerminalTool


class MockMCPTool(BaseTool):
    def __init__(self, name="external_mcp_query"):
        super().__init__(
            metadata=ToolMetadata(
                name=name,
                description="Mock external MCP tool.",
                version="2.1.0",
                permission_level="PUBLIC"
            )
        )

    async def initialize(self):
        self._is_initialized = True

    async def validate(self, params: Dict[str, Any]) -> bool:
        return "query" in params

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"mcp_result": f"Answer for {params['query']}"}

    async def cleanup(self):
        pass

    async def health_check(self) -> ToolHealthStatus:
        return ToolHealthStatus(is_available=True, latency_ms=0.2)


class MockUpgradedTool(BaseTool):
    def __init__(self, name="filesystem"):
        super().__init__(
            metadata=ToolMetadata(
                name=name,
                description="Upgraded filesystem tool v2.",
                version="2.0.0",
                permission_level="STANDARD"
            )
        )

    async def initialize(self):
        self._is_initialized = True

    async def validate(self, params: Dict[str, Any]) -> bool:
        return True

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "upgraded_v2_success"}

    async def cleanup(self):
        pass

    async def health_check(self) -> ToolHealthStatus:
        return ToolHealthStatus(is_available=True, latency_ms=0.1)


class MockSecurityPermManager:
    def verify_tool_permission(self, tool_name: str, level: str, params: Dict[str, Any]) -> bool:
        if level == "HIGH_RISK" and params.get("allow_high_risk") is not True:
            return False
        return True
    def consume_action_confirmation(self, confirmation_id, tool_name, params) -> bool:
        return params.get("allow_high_risk") is True


class TestToolRegistryAndManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.registry = ToolRegistry()
        # Reset registry state between tests
        self.registry.tools.clear()
        self.registry.mcp_servers.clear()
        self.manager = ToolManager()
        self.manager.registry = self.registry
        self.manager.permission_manager = None

    def test_tool1_discovery_and_registration(self):
        """Verify automatic discovery and registration of built-in domain tools."""
        self.registry.discover_and_register_defaults()
        tool_names = [t.name for t in self.registry.list_tools()]
        for expected in ["filesystem", "terminal", "browser", "python", "github", "docker", "calendar", "email"]:
            self.assertIn(expected, tool_names)

    async def test_tool2_uniform_lifecycle(self):
        """Verify full lifecycle execution (`initialize -> validate -> check_permission -> execute`)."""
        self.registry.register_tool(FilesystemTool())

        # Test valid read/list execution
        res = await self.manager.execute_tool("filesystem", {"operation": "list", "path": "."})
        self.assertEqual(res.status, "success")
        self.assertGreaterEqual(res.latency_ms, 0.0)

        # Test validation failure when missing required args
        res_invalid = await self.manager.execute_tool("filesystem", {"operation": "invalid_op"})
        self.assertEqual(res_invalid.status, "validation_error")

    async def test_tool3_permission_checks(self):
        """Verify permission level checks with PermissionManager."""
        import os
        os.environ["BUDDY_ENABLE_TERMINAL_TOOL"] = "true"
        self.registry.register_tool(TerminalTool())
        self.manager.set_permission_manager(MockSecurityPermManager())

        # Should be denied because Terminal is HIGH_RISK and allow_high_risk != True
        res_denied = await self.manager.execute_tool("terminal", {"command": "echo test"})
        self.assertEqual(res_denied.status, "permission_denied")

        # Should succeed when authorized
        res_allowed = await self.manager.execute_tool("terminal", {"command": "echo test", "allow_high_risk": True, "confirmation_id": "valid"})
        self.assertEqual(res_allowed.status, "success")
        self.assertIn("test", res_allowed.output["stdout"])

    async def test_tool4_health_monitoring(self):
        """Verify health check pinging across registered tools."""
        self.registry.discover_and_register_defaults()
        statuses = await self.manager.check_all_health()
        self.assertIn("filesystem", statuses)
        self.assertTrue(statuses["filesystem"].is_available)
        self.assertGreaterEqual(statuses["filesystem"].latency_ms, 0.0)

    async def test_tool5_versioning_and_lifecycle(self):
        """Verify tool installation, upgrade, disabling, and uninstallation."""
        self.registry.register_tool(FilesystemTool())
        self.assertEqual(self.registry.get_tool("filesystem").metadata.version, "1.0.0")

        # Upgrade tool
        await self.manager.upgrade_tool("filesystem", MockUpgradedTool("filesystem"))
        self.assertEqual(self.registry.get_tool("filesystem").metadata.version, "2.0.0")
        res = await self.manager.execute_tool("filesystem", {})
        self.assertEqual(res.output["status"], "upgraded_v2_success")

        # Disable tool
        await self.manager.disable_tool("filesystem")
        res_disabled = await self.manager.execute_tool("filesystem", {})
        self.assertEqual(res_disabled.status, "disabled")

        # Uninstall tool
        self.assertTrue(await self.manager.uninstall_tool("filesystem"))
        self.assertIsNone(self.registry.get_tool("filesystem"))

    async def test_tool6_mcp_compatibility(self):
        """Verify external MCP server tools register cleanly and run through uniform manager."""
        mcp_tools = [MockMCPTool("mcp_search"), MockMCPTool("mcp_fetch")]
        self.registry.register_mcp_server("external_memory_server", mcp_tools)

        self.assertIn("mcp_search", self.registry.mcp_servers["external_memory_server"])
        mcp_meta = self.registry.get_tool("mcp_search").metadata
        self.assertTrue(mcp_meta.is_mcp_compatible)
        self.assertEqual(mcp_meta.mcp_server_name, "external_memory_server")

        res = await self.manager.execute_tool("mcp_search", {"query": "devbuddy"})
        self.assertEqual(res.status, "success")
        self.assertIn("Answer for devbuddy", res.output["mcp_result"])


if __name__ == "__main__":
    unittest.main()

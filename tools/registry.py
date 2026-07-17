"""
Tool Registry for DevBuddy 2.0 (`tools/registry.py`).
Discovers, registers, and exposes metadata for all native tools and external MCP servers.
No agent accesses tools directly or bypasses permission checks.
"""

from typing import Dict, Any, List, Optional
from .base_tool import BaseTool, ToolMetadata


class ToolRegistry:
    """
    Central repository tracking all active tools in the DevBuddy 2.0 ecosystem.
    """

    _instance: Optional["ToolRegistry"] = None

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.mcp_servers: Dict[str, List[str]] = {}

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_tool(self, tool: BaseTool):
        """Register a tool instance."""
        if not tool.metadata.name:
            raise ValueError("Tool name must not be empty.")
        self.tools[tool.metadata.name.lower()] = tool

    def register_mcp_server(self, server_name: str, mcp_tools: List[BaseTool]):
        """
        Register external Model Context Protocol (MCP) tools under a named server without
        requiring any modifications to the cognitive Planner.
        """
        server_key = server_name.lower()
        self.mcp_servers[server_key] = []
        for tool in mcp_tools:
            tool.metadata.is_mcp_compatible = True
            tool.metadata.mcp_server_name = server_name
            self.register_tool(tool)
            self.mcp_servers[server_key].append(tool.metadata.name.lower())

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Retrieve a registered tool by name."""
        return self.tools.get(name.lower())

    def list_tools(self, only_enabled: bool = True) -> List[ToolMetadata]:
        """Return metadata for all registered tools."""
        res = []
        for t in self.tools.values():
            if only_enabled and not t.metadata.is_enabled:
                continue
            res.append(t.metadata)
        return res

    def discover_and_register_defaults(self):
        """Auto-discover and register built-in domain tools."""
        from .filesystem.tool import FilesystemTool
        from .terminal.tool import TerminalTool
        from .browser.tool import BrowserTool
        from .python.tool import PythonTool
        from .github.tool import GitHubTool
        from .docker.tool import DockerTool
        from .calendar.tool import CalendarTool
        from .email.tool import EmailTool

        for t_cls in [
            FilesystemTool, TerminalTool, BrowserTool, PythonTool,
            GitHubTool, DockerTool, CalendarTool, EmailTool
        ]:
            self.register_tool(t_cls())

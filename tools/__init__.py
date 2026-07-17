"""
DevBuddy 2.0 Centralized Tool Registry (`tools/`).
Exposes and orchestrates all external capabilities (filesystem, terminal, browser, git, etc.).
No agent is permitted to access external capabilities directly or bypass the Tool Manager.
"""

from .base_tool import BaseTool, ToolMetadata, ToolHealthStatus

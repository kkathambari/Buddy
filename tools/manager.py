"""
Tool Manager for DevBuddy 2.0 (`tools/manager.py`).
Orchestrates the uniform execution lifecycle across all tools:
initialize -> validate -> check_permission -> execute -> cleanup.
Monitors tool health metrics and supports dynamic installation, upgrade, and disabling.
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .base_tool import BaseTool, ToolMetadata, ToolHealthStatus
from .registry import ToolRegistry
from core.permissions import global_permission_manager


@dataclass
class ToolExecutionResult:
    tool_name: str
    status: str  # "success", "permission_denied", "validation_error", "execution_error", "disabled"
    output: Any
    latency_ms: float
    error_message: Optional[str] = None


class ToolManager:
    """
    Singleton lifecycle and governance manager for external capabilities.
    """

    _instance: Optional["ToolManager"] = None

    def __init__(self):
        self.registry = ToolRegistry.get_instance()
        self.permission_manager = global_permission_manager

    @classmethod
    def get_instance(cls) -> "ToolManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_permission_manager(self, perm_mgr: Any):
        """Link to DevBuddy 2.0 centralized security PermissionManager."""
        self.permission_manager = perm_mgr

    def check_permission(self, tool_name: str, permission_level: str, params: Dict[str, Any]) -> bool:
        """Verify execution authorization."""
        params_for_confirmation = {k: v for k, v in params.items() if k != "confirmation_id"}
        needs_confirmation = (
            permission_level in {"HIGH_RISK", "ADMIN"}
            or (tool_name.lower() == "filesystem" and params.get("operation") in {"write", "delete"})
        )
        if needs_confirmation:
            confirmation_id = params.get("confirmation_id")
            return bool(confirmation_id) and self.permission_manager.consume_action_confirmation(
                confirmation_id, tool_name, params_for_confirmation
            )
        if permission_level == "PUBLIC":
            return True
        if self.permission_manager and hasattr(self.permission_manager, "verify_tool_permission"):
            return self.permission_manager.verify_tool_permission(tool_name, permission_level, params)
        return permission_level == "STANDARD"

    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolExecutionResult:
        """
        Execute tool through full uniform lifecycle:
        1. Lookup tool in registry
        2. Check initialization & enabled status
        3. Validate input schema
        4. Verify security permission
        5. Execute tool logic and measure latency
        """
        start_time = time.time()
        tool = self.registry.get_tool(tool_name)

        if not tool:
            return ToolExecutionResult(
                tool_name=tool_name,
                status="execution_error",
                output=None,
                latency_ms=0.0,
                error_message=f"Tool '{tool_name}' not found in registry."
            )

        if not tool.metadata.is_enabled:
            return ToolExecutionResult(
                tool_name=tool_name,
                status="disabled",
                output=None,
                latency_ms=0.0,
                error_message=f"Tool '{tool_name}' is currently disabled."
            )

        # 1. Initialize if not already set up
        if not tool._is_initialized:
            try:
                await tool.initialize()
                tool._is_initialized = True
            except Exception as exc:
                tool._health.failure_count += 1
                return ToolExecutionResult(
                    tool_name=tool_name,
                    status="execution_error",
                    output=None,
                    latency_ms=(time.time() - start_time) * 1000.0,
                    error_message=f"Tool initialization failed: {str(exc)}"
                )

        # 2. Validate parameters
        try:
            is_valid = await tool.validate(params)
            if not is_valid:
                return ToolExecutionResult(
                    tool_name=tool_name,
                    status="validation_error",
                    output=None,
                    latency_ms=(time.time() - start_time) * 1000.0,
                    error_message="Input parameters failed schema validation."
                )
        except Exception as exc:
            return ToolExecutionResult(
                tool_name=tool_name,
                status="validation_error",
                output=None,
                latency_ms=(time.time() - start_time) * 1000.0,
                error_message=f"Validation error: {str(exc)}"
            )

        # 3. Check Permissions
        if not self.check_permission(tool.metadata.name, tool.metadata.permission_level, params):
            return ToolExecutionResult(
                tool_name=tool_name,
                status="permission_denied",
                output=None,
                latency_ms=(time.time() - start_time) * 1000.0,
                error_message=f"Permission check denied execution of '{tool_name}' (Level: {tool.metadata.permission_level})."
            )

        # 4. Execute with latency & failure monitoring
        try:
            output = await tool.execute(params)
            latency = (time.time() - start_time) * 1000.0
            tool._health.latency_ms = latency
            tool._health.failure_count = 0
            tool._health.is_available = True
            return ToolExecutionResult(
                tool_name=tool_name,
                status="success",
                output=output,
                latency_ms=latency
            )
        except Exception as exc:
            latency = (time.time() - start_time) * 1000.0
            tool._health.failure_count += 1
            if tool._health.failure_count >= 3:
                tool._health.is_available = False
            return ToolExecutionResult(
                tool_name=tool_name,
                status="execution_error",
                output=None,
                latency_ms=latency,
                error_message=str(exc)
            )

    async def check_all_health(self) -> Dict[str, ToolHealthStatus]:
        """Verify ping and latency across all registered tools."""
        statuses = {}
        for name, tool in self.registry.tools.items():
            if not tool.metadata.is_enabled:
                statuses[name] = ToolHealthStatus(is_available=False, dependency_status="disabled")
                continue
            try:
                h = await tool.health_check()
                h.last_checked = time.time()
                tool._health = h
                statuses[name] = h
            except Exception as exc:
                tool._health.is_available = False
                tool._health.failure_count += 1
                tool._health.dependency_status = f"error: {str(exc)}"
                statuses[name] = tool._health
        return statuses

    # Versioning & Lifecycle Operations (TOOL-5)
    def install_tool(self, tool: BaseTool):
        """Install or register a new tool into the active registry."""
        self.registry.register_tool(tool)

    async def upgrade_tool(self, tool_name: str, new_tool: BaseTool) -> bool:
        """Upgrade an existing tool instance cleanly."""
        old = self.registry.get_tool(tool_name)
        if old:
            try:
                await old.cleanup()
            except Exception:
                pass
        self.registry.register_tool(new_tool)
        return True

    async def disable_tool(self, tool_name: str) -> bool:
        """Temporarily disable a tool and clean up allocated resources."""
        t = self.registry.get_tool(tool_name)
        if t:
            t.metadata.is_enabled = False
            try:
                await t.cleanup()
            except Exception:
                pass
            return True
        return False

    async def uninstall_tool(self, tool_name: str) -> bool:
        """Completely remove a tool from the registry."""
        key = tool_name.lower()
        if key in self.registry.tools:
            t = self.registry.tools[key]
            try:
                await t.cleanup()
            except Exception:
                pass
            del self.registry.tools[key]
            return True
        return False

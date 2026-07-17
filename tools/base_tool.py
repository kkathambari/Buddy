"""
Base Tool Interface for DevBuddy 2.0 Tool Registry (`tools/base_tool.py`).
Every tool in the ecosystem must strictly implement this interface:
initialize(), validate(), execute(), cleanup(), and health_check().
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ToolMetadata:
    name: str
    description: str
    version: str = "1.0.0"
    permission_level: str = "STANDARD"  # "PUBLIC", "STANDARD", "HIGH_RISK", "ADMIN"
    input_schema: Dict[str, Any] = field(default_factory=dict)
    is_mcp_compatible: bool = False
    mcp_server_name: Optional[str] = None
    is_enabled: bool = True


@dataclass
class ToolHealthStatus:
    is_available: bool
    latency_ms: float = 0.0
    failure_count: int = 0
    dependency_status: str = "ok"
    last_checked: float = 0.0


class BaseTool(ABC):
    """
    Uniform contract for all tools managed by the Tool Registry.
    """

    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata
        self._is_initialized = False
        self._health = ToolHealthStatus(is_available=True)

    @abstractmethod
    async def initialize(self):
        """Perform necessary setup, resource allocation, or driver checks."""
        pass

    @abstractmethod
    async def validate(self, params: Dict[str, Any]) -> bool:
        """Validate input parameters against required schema before execution."""
        pass

    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Any:
        """Execute the tool's core logic and return structured output."""
        pass

    @abstractmethod
    async def cleanup(self):
        """Release allocated sockets, file handles, or subprocesses."""
        pass

    @abstractmethod
    async def health_check(self) -> ToolHealthStatus:
        """Ping dependencies or check internal availability and latency."""
        pass

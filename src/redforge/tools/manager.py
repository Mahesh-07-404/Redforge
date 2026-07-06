"""Tool service for managing and executing system tools."""

import logging

from ..contracts.tool import ToolCall, ToolResult
from .executor import ToolExecutor
from .installer import ToolInstaller
from .registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolService:
    """Service to handle tool availability, execution routing, and automated installation."""

    def __init__(self):
        self.executor = ToolExecutor()
        self.registry = ToolRegistry()
        self.installer = ToolInstaller()

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """Route and execute a tool call."""
        if not self.installer.is_installed(tool_call.tool_name):
            # ToolInstaller only generates plans; it never executes installs.
            return ToolResult(
                tool_name=tool_call.tool_name,
                command=tool_call.command,
                exit_code=-1,
                stdout="",
                stderr="",
                parsed_output={},
                execution_time_ms=0,
                timed_out=False,
                error=f"Tool '{tool_call.tool_name}' is not installed on this system.",
            )

        return self.executor.execute(tool_call)

    def list_available(self) -> list[str]:
        """List all tools defined in registry."""
        return self.registry.list_available()

    def is_available(self, tool_name: str) -> bool:
        """Check if a tool is registered and installed on the host."""
        return tool_name in self.list_available() and self.installer.is_installed(tool_name)


# Compatibility aliases
ToolManager = ToolService

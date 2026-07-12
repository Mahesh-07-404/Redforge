"""Tool Executor for RedForge"""

import logging

from redforge.prompts.registry import get_prompt_registry

from ..contracts.tool import ToolCall, ToolResult
from .registry import ToolRegistry
from .runner import ToolRunner

logger = logging.getLogger(__name__)


class ToolExecutor:

    def __init__(self) -> None:
        self.runner: ToolRunner = ToolRunner()
        self.registry: ToolRegistry = ToolRegistry()

    def execute(self, tool_call: ToolCall) -> ToolResult:
        if not tool_call.approved:
            return ToolResult(
                tool_name=tool_call.tool_name,
                command=tool_call.command,
                exit_code=-1,
                stdout="",
                stderr="",
                parsed_output={},
                execution_time_ms=0,
                timed_out=False,
                error="Execution denied by autonomy controller",
            )

        # Retrieve and render tool selection prompt for auditing/logging
        try:
            registry = get_prompt_registry()
            rendered = registry.render(
                "execution_tool_selector",
                tools_available=str(self.list_available()),
                task_description=f"Executing tool {tool_call.tool_name} with command {tool_call.command}",
                safety_constraints="Ensure input target validation and safe argument list format",
            )
            logger.debug("Rendered execution tool selector prompt:\n%s", rendered)
        except Exception as e:
            logger.debug("Failed to render tool selector prompt: %s", e)

        return self.runner.run(tool_call)

    def is_available(self, tool_name: str) -> bool:
        return tool_name in self.registry.list_available()

    def list_available(self) -> list[str]:
        return self.registry.list_available()

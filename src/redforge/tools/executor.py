
from ..contracts.tool import ToolCall, ToolResult
from .registry import ToolRegistry
from .runner import ToolRunner


class ToolExecutor:
    def __init__(self):
        self.runner = ToolRunner()
        self.registry = ToolRegistry()

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

        return self.runner.run(tool_call)

    def is_available(self, tool_name: str) -> bool:
        return tool_name in self.registry.list_available()

    def list_available(self) -> list[str]:
        return self.registry.list_available()

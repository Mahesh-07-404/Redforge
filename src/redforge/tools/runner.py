import subprocess  # nosec B404
import time

from ..contracts.tool import ToolCall, ToolResult


class ToolRunner:
    def run(self, tool_call: ToolCall) -> ToolResult:
        start = time.time()
        try:
            proc = subprocess.run(  # nosec B603
                tool_call.command, capture_output=True, text=True, timeout=tool_call.timeout_seconds
            )
            duration = int((time.time() - start) * 1000)
            return ToolResult(
                tool_name=tool_call.tool_name,
                command=tool_call.command,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                parsed_output={},
                execution_time_ms=duration,
                timed_out=False,
                error=None,
            )
        except subprocess.TimeoutExpired as e:
            duration = int((time.time() - start) * 1000)
            return ToolResult(
                tool_name=tool_call.tool_name,
                command=tool_call.command,
                exit_code=-1,
                stdout=e.stdout.decode("utf-8") if e.stdout else "",
                stderr=e.stderr.decode("utf-8") if e.stderr else "",
                parsed_output={},
                execution_time_ms=duration,
                timed_out=True,
                error="Timeout expired",
            )
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            return ToolResult(
                tool_name=tool_call.tool_name,
                command=tool_call.command,
                exit_code=-1,
                stdout="",
                stderr="",
                parsed_output={},
                execution_time_ms=duration,
                timed_out=False,
                error=str(e),
            )

"""RedForge Tool Executor Component"""

import subprocess
import time
from datetime import datetime
from typing import Dict, Any, Optional
from redforge.core.tool_executor import ToolResult

class ToolExecutor:
    """Executes security tools on the terminal, collecting outputs, errors, and exit codes."""

    def __init__(self, safety_engine: Optional[Any] = None):
        self.safety_engine = safety_engine
        self.history = []

    def execute(self, tool_name: str, command: str) -> ToolResult:
        """Execute a shell command, enforce safety checks, and collect outputs"""
        if self.safety_engine:
            # Check command for dangerous patterns
            violation = self.safety_engine.check_command(command)
            if violation and violation.blocked:
                return ToolResult(
                    tool=tool_name,
                    command=command,
                    stdout="",
                    stderr="Command blocked by safety engine",
                    returncode=1,
                    duration_s=0.0,
                    error="Command blocked by safety engine"
                )

        start_time = time.time()
        try:
            process = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )
            duration = time.time() - start_time
            result = ToolResult(
                tool=tool_name,
                command=command,
                stdout=process.stdout,
                stderr=process.stderr,
                returncode=process.returncode,
                duration_s=duration
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            result = ToolResult(
                tool=tool_name,
                command=command,
                stdout="",
                stderr="Command timed out",
                returncode=124,
                duration_s=duration,
                error="Timeout expired"
            )
        except Exception as e:
            duration = time.time() - start_time
            result = ToolResult(
                tool=tool_name,
                command=command,
                stdout="",
                stderr=str(e),
                returncode=1,
                duration_s=duration,
                error=str(e)
            )

        self.history.append(result)
        return result

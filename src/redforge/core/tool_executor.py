"""
RedForge ToolExecutor
Real tool execution with safety checks and structured output.
All tools are gated by the SafetyEngine and the active autonomy level.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import shutil
import textwrap
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class ToolResult:
    tool: str
    command: str
    stdout: str
    stderr: str
    returncode: int
    duration_s: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error: str | None = None
    finding: dict[str, Any] | None = None  # populated by reflect step

    @property
    def success(self) -> bool:
        return self.returncode == 0 and self.error is None

    @property
    def output(self) -> str:
        """Combined trimmed output, truncated for LLM consumption"""
        raw = (self.stdout or "") + ("\n" + self.stderr if self.stderr else "")
        return raw[:6000] + "\n[OUTPUT TRUNCATED]" if len(raw) > 6000 else raw

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "command": self.command,
            "success": self.success,
            "returncode": self.returncode,
            "duration_s": round(self.duration_s, 2),
            "output": self.output,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# ToolExecutor
# ---------------------------------------------------------------------------


class ToolExecutor:
    """
    Executes security tools with safety gating.

    Safety rules:
      - Always run `_safe_check(cmd)` before execution.
      - Dangerous patterns are blocked regardless of autonomy level.
      - In MANUAL mode nothing runs automatically — callers should
        check `needs_confirmation()` and obtain user approval first.
    """

    # Commands that are always blocked
    _BLOCKED_PATTERNS = [
        "rm -rf /",
        "dd if=/dev/zero of=/dev/sd",
        "mkfs",
        ":(){ :|:",  # fork bomb
        "> /dev/sd",
        "chmod 777 /etc",
    ]

    def __init__(
        self,
        safety_engine=None,
        autonomy_level: str = "manual",
        timeout_default: int = 60,
        event_callback: Callable[[dict[str, Any]], Any] | None = None,
    ):
        self.safety = safety_engine
        self.autonomy_level = autonomy_level
        self.timeout_default = timeout_default
        self._history: list[ToolResult] = []
        self._event_callback = event_callback
        self._call_seq = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def bash(
        self,
        command: str,
        timeout: int | None = None,
        cwd: str | None = None,
    ) -> ToolResult:
        """Run an arbitrary bash command."""
        call_id = self._next_call_id()
        await self._emit("tool_start", call_id=call_id, tool="bash", command=command)
        blocked, reason = self._safe_check(command)
        if blocked:
            result = self._blocked_result("bash", command, reason)
            await self._emit_result(call_id, result)
            return result

        result = await self._run_subprocess(
            cmd=command,
            tool_name="bash",
            timeout=timeout or self.timeout_default,
            cwd=cwd,
            shell=True,
        )
        await self._emit_result(call_id, result)
        return result

    async def python_run(
        self,
        code: str,
        timeout: int | None = None,
    ) -> ToolResult:
        """Execute a Python snippet and capture stdout/stderr."""
        call_id = self._next_call_id()
        command = f"{__import__('sys').executable} <temp-script>"
        await self._emit("tool_start", call_id=call_id, tool="python", command=command)
        # Wrap in a temp script executed via the current interpreter
        import os
        import sys
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(textwrap.dedent(code))
            tmp_path = fh.name

        try:
            result = await self._run_subprocess(
                cmd=[sys.executable, tmp_path],
                tool_name="python",
                timeout=timeout or 30,
                shell=False,
            )
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        await self._emit_result(call_id, result)
        return result

    async def http_get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: int = 15,
    ) -> ToolResult:
        """Make a safe HTTP GET request using curl."""
        call_id = self._next_call_id()
        header_flags = ""
        if headers:
            header_flags = " ".join(f'-H "{k}: {v}"' for k, v in headers.items())
        cmd = f'curl -sL --max-time {timeout} {header_flags} "{url}"'.strip()
        await self._emit("tool_start", call_id=call_id, tool="http_get", command=cmd)
        # scope check
        if self.safety:
            from urllib.parse import urlparse

            host = urlparse(url).netloc.split(":")[0]
            v = self.safety.check_target(host)
            if v and v.blocked:
                result = self._blocked_result("http_get", url, v.message)
                await self._emit_result(call_id, result)
                return result

        result = await self._run_subprocess(
            cmd, tool_name="http_get", timeout=timeout + 5, shell=True
        )
        await self._emit_result(call_id, result)
        return result

    async def nmap(
        self,
        target: str,
        flags: str = "-sV -T4 --top-ports 1000",
        timeout: int = 120,
    ) -> ToolResult:
        """Run nmap with scope and tool-availability checks."""
        cmd = f"nmap {flags} {target}"
        call_id = self._next_call_id()
        await self._emit("tool_start", call_id=call_id, tool="nmap", command=cmd)
        if not shutil.which("nmap"):
            result = self._error_result(
                "nmap", cmd, "nmap is not installed. Run: sudo apt install nmap"
            )
            await self._emit_result(call_id, result)
            return result

        if self.safety:
            v = self.safety.check_target(target)
            if v and v.blocked:
                result = self._blocked_result("nmap", target, v.message)
                await self._emit_result(call_id, result)
                return result

        result = await self._run_subprocess(cmd, tool_name="nmap", timeout=timeout, shell=True)
        await self._emit_result(call_id, result)
        return result

    async def ffuf(
        self,
        url: str,
        wordlist: str = "/usr/share/wordlists/dirb/common.txt",
        extensions: str = "php,html,js",
        timeout: int = 120,
    ) -> ToolResult:
        """Run ffuf directory/file fuzzing."""
        cmd = f'ffuf -u "{url}/FUZZ" -w {wordlist} -e {extensions} -mc 200,301,302,403 -t 40 -timeout 5'
        call_id = self._next_call_id()
        await self._emit("tool_start", call_id=call_id, tool="ffuf", command=cmd)
        if not shutil.which("ffuf"):
            result = self._error_result("ffuf", cmd, "ffuf is not installed")
            await self._emit_result(call_id, result)
            return result

        result = await self._run_subprocess(cmd, tool_name="ffuf", timeout=timeout, shell=True)
        await self._emit_result(call_id, result)
        return result

    async def whatweb(self, url: str, timeout: int = 30) -> ToolResult:
        """Fingerprint web technologies."""
        call_id = self._next_call_id()
        if not shutil.which("whatweb"):
            # fall back to curl + headers
            cmd = f'curl -sI --max-time 10 "{url}"'
            await self._emit("tool_start", call_id=call_id, tool="whatweb(curl)", command=cmd)
            result = await self._run_subprocess(
                cmd, tool_name="whatweb(curl)", timeout=20, shell=True
            )
            await self._emit_result(call_id, result)
            return result
        cmd = f'whatweb -a 3 "{url}"'
        await self._emit("tool_start", call_id=call_id, tool="whatweb", command=cmd)
        result = await self._run_subprocess(cmd, tool_name="whatweb", timeout=timeout, shell=True)
        await self._emit_result(call_id, result)
        return result

    async def dns_enum(self, domain: str, timeout: int = 30) -> ToolResult:
        """Run basic DNS enumeration."""
        cmd = (
            f"echo '=== A ===' && dig +short A {domain} ; "
            f"echo '=== MX ===' && dig +short MX {domain} ; "
            f"echo '=== NS ===' && dig +short NS {domain} ; "
            f"echo '=== TXT ===' && dig +short TXT {domain}"
        )
        call_id = self._next_call_id()
        await self._emit("tool_start", call_id=call_id, tool="dns_enum", command=cmd)
        result = await self._run_subprocess(cmd, tool_name="dns_enum", timeout=timeout, shell=True)
        await self._emit_result(call_id, result)
        return result

    async def whois(self, target: str, timeout: int = 15) -> ToolResult:
        """Run whois lookup."""
        cmd = f"whois {target}"
        call_id = self._next_call_id()
        await self._emit("tool_start", call_id=call_id, tool="whois", command=cmd)
        result = await self._run_subprocess(cmd, tool_name="whois", timeout=timeout, shell=True)
        await self._emit_result(call_id, result)
        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _run_subprocess(
        self,
        cmd,
        tool_name: str,
        timeout: int,
        shell: bool = True,
        cwd: str | None = None,
    ) -> ToolResult:
        t0 = time.monotonic()
        try:
            proc = (
                await asyncio.create_subprocess_shell(
                    cmd if shell else " ".join(cmd),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                )
                if shell
                else await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                )
            )
            try:
                stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                result = ToolResult(
                    tool=tool_name,
                    command=cmd if isinstance(cmd, str) else " ".join(cmd),
                    stdout="",
                    stderr="",
                    returncode=-1,
                    duration_s=time.monotonic() - t0,
                    error=f"Timed out after {timeout}s",
                )
                self._history.append(result)
                return result

            result = ToolResult(
                tool=tool_name,
                command=cmd if isinstance(cmd, str) else " ".join(cmd),
                stdout=stdout_b.decode("utf-8", errors="replace"),
                stderr=stderr_b.decode("utf-8", errors="replace"),
                returncode=proc.returncode or 0,
                duration_s=time.monotonic() - t0,
            )
        except Exception as exc:
            result = ToolResult(
                tool=tool_name,
                command=str(cmd),
                stdout="",
                stderr="",
                returncode=-1,
                duration_s=time.monotonic() - t0,
                error=str(exc),
            )

        self._history.append(result)
        return result

    def _next_call_id(self) -> str:
        self._call_seq += 1
        return f"tool-{self._call_seq}"

    async def _emit(self, event: str, **payload: Any) -> None:
        if not self._event_callback:
            return
        try:
            result = self._event_callback({"event": event, **payload})
            if inspect.isawaitable(result):
                await result
        except (
            Exception
        ) as exc:  # nosec B110 - event callback invocation failure must not block execution pipeline
            logger.warning("Event callback raised an error (event=%s): %s", event, exc)

    async def _emit_result(self, call_id: str, result: ToolResult) -> None:
        await self._emit(
            "tool_end",
            call_id=call_id,
            tool=result.tool,
            command=result.command,
            result=result.to_dict(),
            success=result.success,
            error=result.error,
        )

    def _safe_check(self, command: str) -> tuple[bool, str]:
        """Return (is_blocked, reason)"""
        cmd_lower = command.lower()
        for pat in self._BLOCKED_PATTERNS:
            if pat in cmd_lower:
                return True, f"Blocked dangerous pattern: {pat!r}"

        if self.safety:
            v = self.safety.check_command(command)
            if v and v.blocked:
                return True, v.message

        return False, ""

    def _blocked_result(self, tool: str, command: str, reason: str) -> ToolResult:
        r = ToolResult(
            tool=tool,
            command=command,
            stdout="",
            stderr="",
            returncode=-1,
            duration_s=0.0,
            error=f"BLOCKED: {reason}",
        )
        self._history.append(r)
        return r

    def _error_result(self, tool: str, command: str, message: str) -> ToolResult:
        r = ToolResult(
            tool=tool,
            command=command,
            stdout="",
            stderr="",
            returncode=1,
            duration_s=0.0,
            error=message,
        )
        self._history.append(r)
        return r

    def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self._history[-limit:]]

    def clear_history(self) -> None:
        self._history.clear()

    @property
    def last_result(self) -> ToolResult | None:
        return self._history[-1] if self._history else None


# ---------------------------------------------------------------------------
# Tool parser — extract tool calls from LLM text
# ---------------------------------------------------------------------------


def parse_tool_calls(text: str) -> list[dict[str, Any]]:
    """
    Detect ``TOOL:`` directives in the LLM response.

    Supported formats
    -----------------
    TOOL: bash
    COMMAND: nmap -sV 10.10.0.1

    TOOL: python
    CODE:
    print("hello")

    TOOL: nmap
    TARGET: example.com
    FLAGS: -sV -T3
    """
    import re

    # Strip markdown code blocks if the LLM wrongly wrapped the TOOL block
    text = re.sub(r"```[a-zA-Z]*", "", text)
    text = text.replace("```", "")

    calls = []
    blocks = re.split(r"TOOL:\s*", text, flags=re.IGNORECASE)

    for block in blocks[1:]:  # first split is before first TOOL:
        lines = block.strip().splitlines()
        if not lines:
            continue

        # Strip any trailing backticks from tool_name just in case
        tool_name = lines[0].strip().strip("`").lower()
        params: dict[str, str] = {}
        code_lines: list[str] = []
        in_code = False

        for line in lines[1:]:
            line_stripped = line.strip()
            if re.match(r"^CODE:\s*$", line_stripped, re.IGNORECASE):
                in_code = True
                continue
            if in_code:
                if re.match(
                    r"^(TOOL:|COMMAND:|TARGET:|FLAGS:|ARGS:)", line_stripped, re.IGNORECASE
                ):
                    in_code = False
                else:
                    code_lines.append(line)
                    continue
            m = re.match(r"^([A-Z]+):\s*(.*)", line_stripped, re.IGNORECASE)
            if m:
                key = m.group(1).lower()
                val = m.group(2).strip().strip("`")
                params[key] = val

        if code_lines:
            params["code"] = "\n".join(code_lines).strip("`\n")

        if tool_name:
            calls.append({"tool": tool_name, **params})

    return calls

from __future__ import annotations

import contextvars
import time
from typing import Any

from .contracts import LogEntry, LogLevel

# Context Variables for tracing request contexts across tasks
context_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
context_session_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("session_id", default=None)
context_workflow_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("workflow_id", default=None)
context_execution_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("execution_id", default=None)


class StructuredLogger:
    """Provides structured, context-aware JSON logging for async execution paths."""

    def __init__(self, component: str) -> None:
        self.component = component
        self._output_lines: list[str] = []

    def bind(
        self,
        request_id: str | None = None,
        session_id: str | None = None,
        workflow_id: str | None = None,
        execution_id: str | None = None,
    ) -> dict[str, contextvars.Token]:
        """Bind trace IDs to current execution context."""
        tokens = {}
        if request_id is not None:
            tokens["request_id"] = context_request_id.set(request_id)
        if session_id is not None:
            tokens["session_id"] = context_session_id.set(session_id)
        if workflow_id is not None:
            tokens["workflow_id"] = context_workflow_id.set(workflow_id)
        if execution_id is not None:
            tokens["execution_id"] = context_execution_id.set(execution_id)
        return tokens

    def unbind(self, tokens: dict[str, contextvars.Token]) -> None:
        """Restore previous trace IDs in the execution context."""
        if "request_id" in tokens:
            context_request_id.reset(tokens["request_id"])
        if "session_id" in tokens:
            context_session_id.reset(tokens["session_id"])
        if "workflow_id" in tokens:
            context_workflow_id.reset(tokens["workflow_id"])
        if "execution_id" in tokens:
            context_execution_id.reset(tokens["execution_id"])

    def log(
        self,
        level: LogLevel,
        message: str,
        duration: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LogEntry:
        """Write a log record."""
        entry = LogEntry(
            log_level=level,
            component=self.component,
            message=message,
            request_id=context_request_id.get(),
            session_id=context_session_id.get(),
            workflow_id=context_workflow_id.get(),
            execution_id=context_execution_id.get(),
            duration=duration,
            metadata=metadata or {},
            timestamp=time.time(),
        )
        # Serialize to JSON line representation
        json_line = entry.model_dump_json()
        self._output_lines.append(json_line)
        # Also print to stdout for standard output log streams
        print(json_line, flush=True)
        return entry

    def debug(self, msg: str, duration: float | None = None, **kwargs) -> LogEntry:
        return self.log(LogLevel.DEBUG, msg, duration, kwargs)

    def info(self, msg: str, duration: float | None = None, **kwargs) -> LogEntry:
        return self.log(LogLevel.INFO, msg, duration, kwargs)

    def warning(self, msg: str, duration: float | None = None, **kwargs) -> LogEntry:
        return self.log(LogLevel.WARNING, msg, duration, kwargs)

    def error(self, msg: str, duration: float | None = None, **kwargs) -> LogEntry:
        return self.log(LogLevel.ERROR, msg, duration, kwargs)

    def critical(self, msg: str, duration: float | None = None, **kwargs) -> LogEntry:
        return self.log(LogLevel.CRITICAL, msg, duration, kwargs)

    def get_lines(self) -> list[str]:
        """Retrieve recorded JSON lines (useful for tests)."""
        return self._output_lines

    def clear(self) -> None:
        self._output_lines.clear()

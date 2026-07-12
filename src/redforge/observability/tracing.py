from __future__ import annotations

import contextvars
import time
import uuid
from typing import Any

from .contracts import TraceSpan

# Context variables to preserve active trace and parent span across async calls
active_trace_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "active_trace_id", default=None
)
active_parent_span_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "active_parent_span_id", default=None
)


class Tracer:
    """Manages context-aware distributed traces and spans."""

    def __init__(self) -> None:
        self._spans: list[TraceSpan] = []

    def span(self, name: str, attributes: dict[str, Any] | None = None) -> TraceSpanContext:
        """Create a new trace span context manager."""
        return TraceSpanContext(self, name, attributes)

    def record_span(self, span: TraceSpan) -> None:
        """Add finished span to internal storage."""
        self._spans.append(span)

    def get_spans(self) -> list[TraceSpan]:
        """Get all spans recorded in tracer memory."""
        return self._spans

    def clear(self) -> None:
        self._spans.clear()


class TraceSpanContext:
    """Context manager wrapping active Trace Spans."""

    def __init__(
        self,
        tracer: Tracer,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        self.tracer = tracer
        self.name = name
        self.attributes = attributes or {}

        self.span_id = str(uuid.uuid4())
        tid = active_trace_id.get()
        if not tid:
            tid = str(uuid.uuid4())
        self.trace_id = tid

        self.parent_span_id = active_parent_span_id.get()
        self.span: TraceSpan | None = None

        # Save context tokens for restoration
        self._trace_token: contextvars.Token[str | None] | None = None
        self._parent_token: contextvars.Token[str | None] | None = None

    def __enter__(self) -> TraceSpan:
        # Bind this span as the parent for subsequent child spans
        self._trace_token = active_trace_id.set(self.trace_id)
        self._parent_token = active_parent_span_id.set(self.span_id)

        self.span = TraceSpan(
            trace_id=self.trace_id,
            span_id=self.span_id,
            parent_span_id=self.parent_span_id,
            name=self.name,
            start_time=time.time(),
            attributes=self.attributes,
        )
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self.span:
            return

        self.span.end_time = time.time()
        self.span.duration_ms = (self.span.end_time - self.span.start_time) * 1000.0

        if exc_type is not None:
            self.span.attributes["error"] = True
            self.span.attributes["error.message"] = str(exc_val)
            self.span.attributes["error.class"] = exc_type.__name__

        self.tracer.record_span(self.span)

        # Restore previous context states
        if self._trace_token:
            active_trace_id.reset(self._trace_token)
        if self._parent_token:
            active_parent_span_id.reset(self._parent_token)

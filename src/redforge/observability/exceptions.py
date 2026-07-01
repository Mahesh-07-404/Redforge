from __future__ import annotations


class ObservabilityError(Exception):
    """Base exception for all observability and monitoring errors."""

    pass


class MetricError(ObservabilityError):
    """Raised when record metrics collection fails."""

    pass


class TraceError(ObservabilityError):
    """Raised when distributed tracing operations fail."""

    pass


class AuditError(ObservabilityError):
    """Raised when writing to the immutable audit log fails."""

    pass


class AlertError(ObservabilityError):
    """Raised when alert dispatching fails."""

    pass

from __future__ import annotations

from .alerts import AlertsEngine
from .audit import AuditLogger
from .events import EventBus
from .health import HealthMonitor
from .logger import StructuredLogger
from .metrics import MetricsCollector
from .profiler import Profiler
from .tracing import Tracer


class ObservabilityManager:
    """Entry point wrapping RedForge Tracing, Logging, Metrics, Audits, Health and Alerts."""

    def __init__(self, service_name: str = "redforge-core") -> None:
        self.service_name = service_name
        self.logger = StructuredLogger(component=service_name)
        self.metrics = MetricsCollector()
        self.tracer = Tracer()
        self.audit = AuditLogger()
        self.profiler = Profiler(logger=self.logger)
        self.alerts = AlertsEngine(logger=self.logger)
        self.health = HealthMonitor()
        self.events = EventBus()

        # Register default health checkers
        self._register_default_checkers()

    def _register_default_checkers(self) -> None:
        """Register default resource checks on initialization."""
        from .contracts import ComponentHealth, HealthState

        # CPU Health Check
        def check_cpu() -> ComponentHealth:
            status = self.health._get_system_resources()
            state = HealthState.HEALTHY
            msg = None
            if status.cpu_percent > 90.0:
                state = HealthState.DEGRADED
                msg = f"High CPU utilization: {status.cpu_percent}%"
            return ComponentHealth(
                name="cpu",
                state=state,
                message=msg,
                latency_ms=0.0,
            )

        # Memory Health Check
        def check_memory() -> ComponentHealth:
            status = self.health._get_system_resources()
            state = HealthState.HEALTHY
            msg = None
            if status.memory_percent > 90.0:
                state = HealthState.UNHEALTHY
                msg = f"Critical memory consumption: {status.memory_percent}%"
            return ComponentHealth(
                name="memory",
                state=state,
                message=msg,
                latency_ms=0.0,
            )

        self.health.register_checker("cpu", check_cpu)
        self.health.register_checker("memory", check_memory)

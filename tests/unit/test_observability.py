from __future__ import annotations

import json
import time
import pytest
from redforge.observability import (
    ObservabilityManager,
    LogLevel,
    AuditStatus,
    AlertSeverity,
    HealthState,
    GrafanaDashboardGenerator,
)


def test_structured_logging_with_context() -> None:
    mgr = ObservabilityManager(service_name="test-service")
    logger = mgr.logger

    # Bind request and session IDs
    tokens = logger.bind(request_id="req-123", session_id="sess-456")
    try:
        # Emit logs
        logger.info("Starting reconnaissance probe", scan_target="127.0.0.1")
        logger.error("Port scanner timed out", duration=5.4)
    finally:
        logger.unbind(tokens)

    lines = logger.get_lines()
    assert len(lines) == 2

    # Verify structured fields
    entry1 = json.loads(lines[0])
    assert entry1["log_level"] == "INFO"
    assert entry1["component"] == "test-service"
    assert entry1["message"] == "Starting reconnaissance probe"
    assert entry1["request_id"] == "req-123"
    assert entry1["session_id"] == "sess-456"
    assert entry1["metadata"]["scan_target"] == "127.0.0.1"

    entry2 = json.loads(lines[1])
    assert entry2["log_level"] == "ERROR"
    assert entry2["duration"] == 5.4


def test_metrics_collection_and_prometheus_export() -> None:
    mgr = ObservabilityManager()
    metrics = mgr.metrics

    metrics.increment("redforge_api_requests_total", labels={"method": "GET", "path": "/health"})
    metrics.increment("redforge_api_requests_total", labels={"method": "GET", "path": "/health"})
    metrics.set_gauge("redforge_active_workers", 4)
    metrics.record_histogram("redforge_workflow_duration_seconds", 12.5)
    metrics.record_histogram("redforge_workflow_duration_seconds", 7.5)

    recs = metrics.get_metrics()
    assert len(recs) == 5

    # Export Prometheus
    prom_data = metrics.export_prometheus()
    assert "redforge_api_requests_total{method=\"GET\",path=\"/health\"} 2" in prom_data
    assert "redforge_active_workers 4" in prom_data
    assert "redforge_workflow_duration_seconds_sum 20" in prom_data
    assert "redforge_workflow_duration_seconds_count 2" in prom_data


def test_tracing_context_spans() -> None:
    mgr = ObservabilityManager()
    tracer = mgr.tracer

    # Span nesting: Root -> Child -> SubChild
    with tracer.span("Conversation") as root:
        assert root.trace_id is not None
        assert root.parent_span_id is None
        
        with tracer.span("Reasoning") as child:
            assert child.trace_id == root.trace_id
            assert child.parent_span_id == root.span_id
            
            with tracer.span("Planner") as sub_child:
                assert sub_child.trace_id == root.trace_id
                assert sub_child.parent_span_id == child.span_id

    spans = tracer.get_spans()
    # Entered and exited in reverse order: Planner -> Reasoning -> Conversation
    assert len(spans) == 3
    assert spans[0].name == "Planner"
    assert spans[1].name == "Reasoning"
    assert spans[2].name == "Conversation"
    assert spans[2].duration_ms >= 0.0


def test_immutable_cryptographic_audit_log() -> None:
    mgr = ObservabilityManager()
    audit = mgr.audit

    # Record audit events
    audit.record(
        event_type="AUTH", actor="operator-1", action="login", status=AuditStatus.SUCCESS
    )
    audit.record(
        event_type="SESSION", actor="operator-1", action="create_session", status=AuditStatus.SUCCESS
    )
    audit.record(
        event_type="PLUGIN", actor="operator-1", action="install_plugin", status=AuditStatus.SUCCESS
    )

    # Initial verification should be perfectly valid
    assert audit.verify_chain() is True

    entries = audit.get_entries()
    assert len(entries) == 3

    # Tamper with an entry (modify actor)
    entries[1].actor = "unauthorized-actor"
    # Verification should now fail due to broken cryptographic chain signature
    assert audit.verify_chain() is False


def test_profiler_operation() -> None:
    mgr = ObservabilityManager()
    profiler = mgr.profiler
    profiler.slow_threshold_seconds = 0.05  # Trigger alert for anything > 50ms

    with profiler.profile("slow-scanning"):
        time.sleep(0.08)  # Exceeds threshold

    profiles = profiler.get_profiles()
    assert len(profiles) == 1
    assert profiles[0]["duration_seconds"] >= 0.08
    assert profiles[0]["name"] == "slow-scanning"


def test_alerts_engine_dispatch() -> None:
    mgr = ObservabilityManager()
    alerts = mgr.alerts

    triggered_alerts = []
    def custom_handler(alert):
        triggered_alerts.append(alert)

    alerts.register_handler(custom_handler)

    # Trigger alerts
    alert1 = alerts.trigger(
        severity=AlertSeverity.CRITICAL,
        title="Worker Node Fail",
        message="Distributed worker worker-1 dropped heartbeat connection.",
        source="heartbeat-monitor",
    )
    
    assert len(alerts.list_active()) == 1
    assert len(triggered_alerts) == 1
    assert triggered_alerts[0].alert_id == alert1.alert_id

    # Resolve alert
    alerts.resolve(alert1.alert_id)
    assert len(alerts.list_active()) == 0
    assert alerts.list_all()[0].resolved is True


def test_health_monitor_diagnostics() -> None:
    mgr = ObservabilityManager()
    monitor = mgr.health

    from redforge.observability.contracts import ComponentHealth, HealthState
    
    # Custom health checker
    def check_db() -> ComponentHealth:
        return ComponentHealth(name="database", state=HealthState.HEALTHY, latency_ms=1.2)

    monitor.register_checker("database", check_db)

    status = monitor.get_status()
    # Check default cpu and memory checks are also present
    comp_names = [c.name for c in status.components]
    assert "database" in comp_names
    assert "cpu" in comp_names
    assert "memory" in comp_names
    
    assert status.resources.cpu_percent is not None
    assert status.resources.memory_percent is not None


def test_grafana_dashboard_schema_export() -> None:
    dashboard_str = GrafanaDashboardGenerator.generate("Custom RedForge Metrics")
    dashboard = json.loads(dashboard_str)
    assert dashboard["title"] == "Custom RedForge Metrics"
    assert len(dashboard["panels"]) > 0
    assert dashboard["style"] == "dark"

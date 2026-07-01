# RedForge Observability & Monitoring Platform

This document describes the design, configuration, and operation of the Observability & Monitoring Platform introduced in Phase 19.

---

## Sub-Components

The observability package (`src/redforge/observability/`) integrates logging, tracing, auditing, and health checks:

1. **ObservabilityManager** ([manager.py](file:///home/mahesh/RedForge/src/redforge/observability/manager.py)):
   The unified orchestrator wrapping all telemetry engines and registering default system resource checkers.
2. **StructuredLogger** ([logger.py](file:///home/mahesh/RedForge/src/redforge/observability/logger.py)):
   Emits context-aware, structured JSON logs. Automatically propagates `request_id`, `session_id`, `workflow_id`, and `execution_id` across asynchronous boundaries using context variables.
3. **MetricsCollector** ([metrics.py](file:///home/mahesh/RedForge/src/redforge/observability/metrics.py)):
   Tracks operational gauges, counters, and histograms (API requests, workflow latency, worker counts). Offers a `/metrics` scrape response exportable to **Prometheus** and **Grafana**.
4. **Tracer** ([tracing.py](file:///home/mahesh/RedForge/src/redforge/observability/tracing.py)):
   Manages parent-child span contexts to build request trace logs traversing from `Conversation` to `Evidence` and `Reporting`.
5. **AuditLogger** ([audit.py](file:///home/mahesh/RedForge/src/redforge/observability/audit.py)):
   Maintains an immutable operations ledger. Implements a cryptographic SHA-256 hash chain verifying that records have not been tampered with or removed.
6. **Profiler** ([profiler.py](file:///home/mahesh/RedForge/src/redforge/observability/profiler.py)):
   Measures processing duration, CPU percent deltas, and process memory RSS deltas to detect slow operations.
7. **AlertsEngine** ([alerts.py](file:///home/mahesh/RedForge/src/redforge/observability/alerts.py)):
   Tracks system warnings, dispatches callback handlers, and manages resolving flags.
8. **HealthMonitor** ([health.py](file:///home/mahesh/RedForge/src/redforge/observability/health.py)):
   Compiles overall health state diagnostics by querying host CPU, memory, disk usage, and registered component checkers.
9. **EventBus** ([events.py](file:///home/mahesh/RedForge/src/redforge/observability/events.py)):
   Implements a Pub/Sub event bus supporting wildcards.
10. **GrafanaDashboardGenerator** ([dashboard.py](file:///home/mahesh/RedForge/src/redforge/observability/dashboard.py)):
    Exports importing-ready Grafana JSON dashboards containing telemetry timeseries and gauges.

---

## Immutable Cryptographic Hash Chain

To ensure audits are immutable, every audit log entry is linked to its predecessor using a SHA-256 hash chain:

$$Signature_n = SHA256(EventID_n \mathbin{\Vert} EventType_n \mathbin{\Vert} Action_n \mathbin{\Vert} PrevSignature_{n-1})$$

The `verify_chain()` method recalculates the chain hash signature sequentially. If any record's payload or execution sequence is modified, the signature check fails immediately, detecting tampering.

---

## Developer Guide & Testing

Run the observability test suite with:

```bash
pytest tests/unit/test_observability.py
```

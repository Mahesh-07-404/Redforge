# RedForge API Gateway Reference Manual

This document details the REST endpoints and WebSocket channels exposed by the RedForge API Gateway.

---

## 1. REST Endpoints

### Health & Monitoring
* `GET /api/v1/health`: Checks system health status, returning a HealthResponse.
* `GET /api/v1/system/info`: Exposes server runtime metadata.
* `GET /metrics`: Returns Prometheus telemetry scraper details.

### Target Sessions
* `GET /api/v1/sessions`: Lists all created sessions.
* `POST /api/v1/sessions`: Create a new session.
* `DELETE /api/v1/sessions/{id}`: Delete a session.

### Agent Chat
* `POST /api/v1/chat`: Dispatch a single non-streaming prompt.

### Workflows
* `GET /api/v1/workflows`: Lists all available modular workflow templates.
* `POST /api/v1/workflows/run`: Launch a target workflow execution.

### Memory Note repository
* `POST /api/v1/memory/store`: Store note contexts.
* `POST /api/v1/memory/query`: Search RAG database entries.

---

## 2. WebSocket Channels

WebSockets enable real-time bidirectional streams and output pipelines:

* `/ws/chat`: Real-time chatbot interface. Stream token updates dynamically.
* `/ws/workflow`: Workflow progression updates (reports active execution rates and completed stages).
* `/ws/execution`: Real-time tool output logger (streams stdout/stderr lines from subprocess executions).

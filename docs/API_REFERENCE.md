# RedForge API Reference — Phase 16: Unified API Gateway

**Version**: 2.0.0  
**Base URL**: `http://127.0.0.1:8000`  
**API Prefix**: `/api/v1`  
**OpenAPI UI**: `http://127.0.0.1:8000/docs`  
**ReDoc UI**: `http://127.0.0.1:8000/redoc`

---

## Standard Response Envelope

Every REST endpoint returns this envelope:

```json
{
  "request_id": "uuid",
  "timestamp": "2026-06-29T12:00:00Z",
  "status": "success",
  "version": "2.0.0",
  "duration_ms": 12.5,
  "payload": { ... },
  "errors": []
}
```

---

## Authentication

| Method | Header | Example |
|---|---|---|
| Bearer JWT | `Authorization: Bearer <token>` | Token from `POST /api/v1/auth/token` |
| API Key | `X-API-Key: <key>` | Key from `POST /api/v1/auth/api-keys` |

> **Note**: Auth is **disabled by default** for local single-user use.  
> Enable with `REDFORGE_API_AUTH__ENABLED=true`.

---

## Health & Observability

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Basic health check (always 200 while alive) |
| GET | `/api/v1/health` | Versioned health check |
| GET | `/ready` | Readiness probe — checks all subsystems |
| GET | `/live` | Liveness probe — always 200 |
| GET | `/version` | Version information |
| GET | `/metrics` | Application metrics |

### Example: Health
```http
GET /api/v1/health

HTTP/1.1 200 OK
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2026-06-29T12:00:00Z",
  "uptime_seconds": 3600.0
}
```

---

## Authentication Endpoints

### Issue JWT Token

```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "username": "admin",
  "password": "secret"
}

→ 200 OK
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Create API Key

```http
POST /api/v1/auth/api-keys
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "name": "ci-pipeline-key",
  "scopes": ["read", "execute"],
  "expires_days": 90
}

→ 201 Created
{
  "key_id": "uuid",
  "api_key": "rf_...",
  "name": "ci-pipeline-key",
  "scopes": ["read", "execute"]
}
```

---

## Sessions

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/sessions` | Create session |
| GET | `/api/v1/sessions` | List sessions (paginated) |
| GET | `/api/v1/sessions/{id}` | Get session |
| PATCH | `/api/v1/sessions/{id}` | Update session |
| DELETE | `/api/v1/sessions/{id}` | Delete session |
| POST | `/api/v1/sessions/{id}/archive` | Archive session |

### Create Session

```http
POST /api/v1/sessions
Content-Type: application/json

{
  "mode": "bugbounty",
  "target": "example.com",
  "autonomy": "manual",
  "name": "My Bug Bounty Session"
}

→ 201 Created
{
  "id": "sess-abc123",
  "mode": "bugbounty",
  "target": "example.com",
  "autonomy": "manual",
  "status": "active",
  "created_at": "2026-06-29T12:00:00Z"
}
```

**Modes**: `bugbounty`, `ctf`, `pentest`, `learning`, `coding`, `android`  
**Autonomy**: `manual`, `semi`, `full`

---

## Chat & Conversation

### Non-Streaming Chat (REST)

```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "scan example.com for open ports",
  "session_id": "sess-abc123",
  "stream": false
}

→ 200 OK
{
  "session_id": "sess-abc123",
  "message": "I'll scan example.com using nmap...",
  "intent": {"type": "scan", "target": "example.com"},
  "plan": { ... },
  "findings": []
}
```

### Get Conversation History

```http
GET /api/v1/conversations/{session_id}?limit=50

→ 200 OK
{
  "session_id": "sess-abc123",
  "messages": [
    {"role": "user", "content": "scan example.com", "timestamp": "..."},
    {"role": "assistant", "content": "Running nmap...", "timestamp": "..."}
  ],
  "total": 2
}
```

---

## Workflows

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/workflows` | List workflow definitions |
| POST | `/api/v1/workflows/run` | Start a workflow |
| GET | `/api/v1/workflows/{id}` | Get workflow details |

### Start Workflow

```http
POST /api/v1/workflows/run
Content-Type: application/json

{
  "workflow_id": "passive_recon",
  "target": "example.com",
  "session_id": "sess-abc123"
}

→ 201 Created
{
  "workflow_id": "passive_recon",
  "run_id": "run-xyz789",
  "status": "running",
  "session_id": "sess-abc123",
  "started_at": "2026-06-29T12:00:00Z"
}
```

**Built-in workflows**: `passive_recon`, `active_recon`, `web_pentest`, `bug_bounty`, `ctf`, `learning`, `report_generation`, `research`

---

## Planner

```http
POST /api/v1/planner/plan
Content-Type: application/json

{
  "session_id": "sess-abc123",
  "intent": {
    "type": "scan",
    "target": "example.com",
    "risk": "medium"
  }
}

→ 200 OK
{
  "plan_id": "plan-001",
  "summary": "Perform comprehensive port scan of example.com",
  "phases": [
    {
      "id": "recon",
      "name": "Reconnaissance",
      "steps": [
        {"id": "s1", "description": "DNS enumeration", "tool": "subfinder"}
      ]
    }
  ]
}
```

---

## Reasoning

```http
POST /api/v1/reasoning/decide
Content-Type: application/json

{
  "session_id": "sess-abc123",
  "goal": "Find XSS vulnerabilities in example.com"
}

→ 200 OK
{
  "reasoning_id": "reason-001",
  "decision": "Begin with passive recon, then targeted XSS probing",
  "strategy": "bottom-up",
  "confidence": 0.87,
  "next_actions": ["subfinder", "httpx", "dalfox"]
}
```

---

## Execution

```http
POST /api/v1/execution/run
Content-Type: application/json

{
  "session_id": "sess-abc123",
  "tool": "nmap",
  "command": ["nmap", "-sV", "example.com"],
  "timeout": 60
}

→ 200 OK
{
  "execution_id": "exec-001",
  "tool": "nmap",
  "status": "completed",
  "stdout": "Starting Nmap 7.94...\n...",
  "stderr": "",
  "exit_code": 0,
  "duration_ms": 4230.5,
  "findings": []
}
```

---

## Reports

```http
POST /api/v1/reports/generate
Content-Type: application/json

{
  "session_id": "sess-abc123",
  "format": "markdown",
  "include_evidence": true,
  "include_remediation": true
}

→ 200 OK
{
  "report_id": "rpt-001",
  "format": "markdown",
  "title": "RedForge Security Report — Session sess-abc123",
  "content": "# Security Report\n\n## Findings\n...",
  "finding_count": 3,
  "severity_summary": {"critical": 0, "high": 1, "medium": 2, "low": 0}
}
```

**Formats**: `markdown`, `json`, `html`, `pdf`

### Get Raw Markdown

```http
GET /api/v1/reports/{session_id}/markdown

→ 200 OK
Content-Type: text/markdown

# RedForge Security Report
...
```

---

## Memory

```http
POST /api/v1/memory/store
{
  "session_id": "sess-abc123",
  "content": "Found SQL injection in /login endpoint",
  "tier": "short"
}

POST /api/v1/memory/query
{
  "session_id": "sess-abc123",
  "query": "SQL injection findings",
  "top_k": 5
}

DELETE /api/v1/memory/session/{session_id}   # flush
```

---

## Plugins

| Method | Path | Auth |
|---|---|---|
| GET | `/api/v1/plugins` | read |
| POST | `/api/v1/plugins/install` | **admin** |
| POST | `/api/v1/plugins/{id}/enable` | **admin** |
| POST | `/api/v1/plugins/{id}/disable` | **admin** |
| DELETE | `/api/v1/plugins/{id}` | **admin** |

---

## MCP (Model Context Protocol)

```http
GET /api/v1/mcp/discover     # all tools + resources
GET /api/v1/mcp/tools        # tool list
GET /api/v1/mcp/resources    # resource list
```

---

## System

```http
GET /api/v1/system/info      # runtime + version info
GET /api/v1/auth/api-keys    # list API keys (admin)
```

---

## WebSocket Streaming Endpoints

All WebSockets accept JSON messages and return JSON events.

| Path | Direction | Purpose |
|---|---|---|
| `/ws/chat` | Bidirectional | Live chat token streaming |
| `/ws/workflow` | Bidirectional | Workflow stage progress |
| `/ws/execution` | Bidirectional | Tool stdout/stderr streaming |
| `/ws/events` | Bidirectional | Generic session event bus |
| `/ws/reasoning` | Bidirectional | Reasoning step streaming |
| `/ws/report` | Bidirectional | Report section streaming |

### WebSocket: /ws/chat

```javascript
// Connect
const ws = new WebSocket("ws://127.0.0.1:8000/ws/chat");

// Send
ws.send(JSON.stringify({
  "session_id": "sess-abc123",
  "message": "scan example.com"
}));

// Events received:
// {"event_type": "chat_start", "session_id": "...", "message": "scan example.com"}
// {"event_type": "token", "session_id": "...", "token": "I'll "}
// {"event_type": "token", "token": "scan "}
// ...
// {"event_type": "done", "session_id": "..."}
```

### WebSocket: /ws/events

```javascript
const ws = new WebSocket("ws://127.0.0.1:8000/ws/events");

// Received on connect:
// {"event_type": "connected", "message": "Subscribed to events"}

// Subscribe to specific session
ws.send(JSON.stringify({"action": "subscribe", "session_id": "sess-abc123"}));

// Ping/Pong
ws.send(JSON.stringify({"action": "ping"}));
// → {"event_type": "pong"}
```

### WebSocket: /ws/execution

```javascript
ws.send(JSON.stringify({
  "session_id": "sess-abc123",
  "tool": "nmap",
  "command": ["nmap", "-sV", "example.com"]
}));

// Events:
// {"event_type": "execution_start", "tool": "nmap", ...}
// {"event_type": "output", "line": "Starting Nmap...", "stream": "stdout"}
// {"event_type": "execution_done", "exit_code": 0, "status": "completed"}
```

---

## Error Responses

All errors return a structured response:

```json
{
  "error_code": "SESSION_NOT_FOUND",
  "message": "Session 'abc' not found.",
  "details": {},
  "trace_id": "uuid"
}
```

| Code | HTTP | Error Code |
|---|---|---|
| Bad Request | 400 | `BAD_REQUEST` |
| Unauthorized | 401 | `AUTHENTICATION_FAILED` |
| Forbidden | 403 | `FORBIDDEN` |
| Not Found | 404 | `NOT_FOUND` |
| Rate Limited | 429 | `RATE_LIMIT_EXCEEDED` |
| Server Error | 500 | `INTERNAL_ERROR` |
| Unavailable | 503 | `SERVICE_UNAVAILABLE` |

---

## Request Pipeline

```
Incoming Request
  ↓
CORS Middleware
  ↓
Security Headers (X-Content-Type-Options, X-Frame-Options, CSP, ...)
  ↓
Request Timing (X-Process-Time header)
  ↓
Structured Logging (method, path, status, duration_ms, request_id, trace_id)
  ↓
Rate Limiter (token-bucket per IP, per endpoint)
  ↓
Payload Size Guard (reject >10MB)
  ↓
Authentication (Bearer JWT / API Key → inject auth_info)
  ↓
Request ID Injection (X-Request-ID, X-Trace-ID)
  ↓
Route Handler
  ↓
Standard Response Envelope
```

---

## Configuration

### Environment Variables

```bash
REDFORGE_API_HOST=127.0.0.1
REDFORGE_API_PORT=8000
REDFORGE_API_DEBUG=false
REDFORGE_API_AUTH__ENABLED=false
REDFORGE_API_AUTH__JWT__SECRET_KEY=your-secret-key
REDFORGE_API_RATE_LIMIT__ENABLED=true
REDFORGE_API_RATE_LIMIT__REQUESTS_PER_MINUTE=60
REDFORGE_API_CORS__ALLOW_ORIGINS=["*"]
```

### Starting the Server

```bash
# Direct Python
from redforge.api import run_server
run_server(host="0.0.0.0", port=8000)

# Or uvicorn
uvicorn redforge.api.app:create_app --factory --host 0.0.0.0 --port 8000

# Or the server module
python -m redforge.api.server
```

---

## RBAC Roles & Scopes

| Role | Scopes |
|---|---|
| `admin` | read, write, execute, report, admin, plugin, mcp, session |
| `operator` | read, write, execute, report, session |
| `analyst` | read, report, session |
| `viewer` | read |

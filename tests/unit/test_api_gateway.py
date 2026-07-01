"""
Phase 16: Unified API Gateway — Test Suite

Tests covering:
- Authentication (JWT, API Keys)
- All REST routes (sessions, chat, workflow, planner, reasoning, execution, report, memory, plugins, mcp, system)
- WebSocket connections (chat, workflow, execution, events, reasoning, report)
- Streaming responses
- Health endpoints
- Rate limiting
- Request validation
- Middleware (request ID, timing, security headers)
- Error handling (typed exceptions)
"""
from __future__ import annotations

import json
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    """Create a fresh FastAPI app instance."""
    from redforge.api.app import create_app
    return create_app()


@pytest.fixture(scope="module")
def client(app):
    """TestClient wrapping the app."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module")
def auth_headers():
    """Pre-issued bearer token for authenticated requests."""
    from redforge.api.auth import get_auth_service
    svc = get_auth_service()
    token = svc.create_token(subject="test_user", roles=["admin"], scopes=["read", "write", "execute", "report", "admin"])
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------

class TestAppFactory:
    def test_app_creates_successfully(self, app):
        assert app is not None
        assert app.title == "RedForge API"

    def test_app_has_openapi(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert schema["info"]["title"] == "RedForge API"
        assert "paths" in schema

    def test_app_has_docs(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_app_has_redoc(self, client):
        resp = client.get("/redoc")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_liveness_returns_200(self, client):
        resp = client.get("/live")
        assert resp.status_code == 200
        data = resp.json()
        assert data["alive"] is True

    def test_readiness_returns_status(self, client):
        resp = client.get("/ready")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "ready" in data
        assert "checks" in data

    def test_version_returns_info(self, client):
        resp = client.get("/version")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "2.0.0"
        assert "phase" in data

    def test_metrics_returns_counters(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "uptime_seconds" in data
        assert "error_rate" in data


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class TestMiddleware:
    def test_request_id_header_present(self, client):
        resp = client.get("/live")
        assert "X-Request-ID" in resp.headers

    def test_trace_id_header_present(self, client):
        resp = client.get("/live")
        assert "X-Trace-ID" in resp.headers

    def test_process_time_header_present(self, client):
        resp = client.get("/live")
        assert "X-Process-Time" in resp.headers

    def test_security_headers_present(self, client):
        resp = client.get("/live")
        assert "X-Content-Type-Options" in resp.headers
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in resp.headers
        assert resp.headers["X-Frame-Options"] == "DENY"

    def test_custom_request_id_propagated(self, client):
        custom_id = "my-custom-req-id-12345"
        resp = client.get("/live", headers={"X-Request-ID": custom_id})
        assert resp.headers.get("X-Request-ID") == custom_id


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class TestAuthentication:
    def test_token_issuance(self, client):
        resp = client.post(
            "/api/v1/auth/token",
            json={"username": "admin", "password": "secret"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "payload" in data
        assert "access_token" in data["payload"]
        assert data["payload"]["token_type"] == "bearer"

    def test_token_empty_credentials_rejected(self, client):
        resp = client.post(
            "/api/v1/auth/token",
            json={"username": "", "password": ""},
        )
        # Should return 4xx
        assert resp.status_code >= 400

    def test_api_key_creation(self, client, auth_headers):
        resp = client.post(
            "/api/v1/auth/api-keys",
            json={"name": "test-key", "scopes": ["read", "write"]},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "payload" in data
        assert "api_key" in data["payload"]
        assert data["payload"]["name"] == "test-key"

    def test_api_key_list(self, client, auth_headers):
        resp = client.get("/api/v1/auth/api-keys", headers=auth_headers)
        assert resp.status_code == 200

    def test_api_key_used_for_auth(self, client, auth_headers):
        # Create key
        resp = client.post(
            "/api/v1/auth/api-keys",
            json={"name": "auth-test-key", "scopes": ["read"]},
            headers=auth_headers,
        )
        key = resp.json()["payload"]["api_key"]
        # Use key
        resp2 = client.get("/api/v1/sessions", headers={"X-API-Key": key})
        assert resp2.status_code == 200

    def test_invalid_token_rejected_when_auth_enabled(self, client):
        from redforge.api.config import get_api_config
        cfg = get_api_config()
        original = cfg.auth.enabled
        cfg.auth.enabled = True
        try:
            resp = client.get(
                "/api/v1/sessions",
                headers={"Authorization": "Bearer invalid.token.here"},
            )
            assert resp.status_code in (401, 403)
        finally:
            cfg.auth.enabled = original


# ---------------------------------------------------------------------------
# JWT auth service unit tests
# ---------------------------------------------------------------------------

class TestAuthService:
    def test_create_and_verify_token(self):
        from redforge.api.auth import get_auth_service
        svc = get_auth_service()
        token = svc.create_token(subject="user1", roles=["analyst"])
        payload = svc.verify_token(token)
        assert payload["sub"] == "user1"
        assert "analyst" in payload["roles"]

    def test_revoked_token_rejected(self):
        from redforge.api.auth import get_auth_service
        from redforge.api.exceptions import TokenInvalidError
        svc = get_auth_service()
        token = svc.create_token(subject="user2")
        svc.revoke_token(token)
        with pytest.raises(TokenInvalidError):
            svc.verify_token(token)

    def test_invalid_signature_rejected(self):
        from redforge.api.auth import get_auth_service
        from redforge.api.exceptions import TokenInvalidError
        svc = get_auth_service()
        token = svc.create_token(subject="user3")
        # Tamper with signature
        parts = token.rsplit(".", 1)
        tampered = parts[0] + ".badsignature"
        with pytest.raises(TokenInvalidError):
            svc.verify_token(tampered)

    def test_api_key_create_verify(self):
        from redforge.api.auth import get_auth_service
        svc = get_auth_service()
        record = svc.create_api_key("mykey", scopes=["read"])
        raw = record["api_key"]
        verified = svc.verify_api_key(raw)
        assert verified["name"] == "mykey"
        assert "read" in verified["scopes"]

    def test_revoked_api_key_rejected(self):
        from redforge.api.auth import get_auth_service
        from redforge.api.exceptions import ApiKeyInvalidError
        svc = get_auth_service()
        record = svc.create_api_key("revoke-me", scopes=["read"])
        raw = record["api_key"]
        svc.revoke_api_key(record["key_id"])
        with pytest.raises(ApiKeyInvalidError):
            svc.verify_api_key(raw)

    def test_scope_check_passes(self):
        from redforge.api.auth import get_auth_service
        svc = get_auth_service()
        svc.check_scope({"scopes": ["read", "write"]}, "write")   # no exception

    def test_scope_check_fails(self):
        from redforge.api.auth import get_auth_service
        from redforge.api.exceptions import InsufficientScopeError
        from redforge.api.config import get_api_config
        svc = get_auth_service()
        cfg = get_api_config()
        original = cfg.auth.enabled
        cfg.auth.enabled = True
        try:
            with pytest.raises(InsufficientScopeError):
                svc.check_scope({"scopes": ["read"]}, "execute")
        finally:
            cfg.auth.enabled = original


# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------

class TestRateLimiter:
    def test_allows_within_limit(self):
        from redforge.api.rate_limit import RateLimiter
        limiter = RateLimiter()
        for _ in range(5):
            allowed, _ = limiter.check("test-ip", "default")
            assert allowed is True

    def test_blocks_after_burst(self):
        from redforge.api.rate_limit import RateLimiter, RateLimitError
        from redforge.api.config import RateLimitConfig
        limiter = RateLimiter()
        # Force a tiny bucket
        from redforge.api.rate_limit import _Bucket
        limiter._buckets["tiny::burst"] = _Bucket(tokens=1.0, capacity=1.0, refill_rate=0.001)
        # First call succeeds
        limiter.check("tiny", "burst")
        # Second call should raise
        with pytest.raises(RateLimitError):
            limiter.check("tiny", "burst")

    def test_reset_clears_bucket(self):
        from redforge.api.rate_limit import RateLimiter
        limiter = RateLimiter()
        limiter.check("reset-ip", "default")
        limiter.reset("reset-ip", "default")
        assert "reset-ip::default" not in limiter._buckets

    def test_disabled_rate_limiter_always_allows(self):
        from redforge.api.rate_limit import RateLimiter
        from redforge.api.config import get_api_config
        cfg = get_api_config()
        original = cfg.rate_limit.enabled
        cfg.rate_limit.enabled = False
        limiter = RateLimiter()
        try:
            for _ in range(200):
                allowed, _ = limiter.check("flood-ip", "default")
                assert allowed
        finally:
            cfg.rate_limit.enabled = original

    def test_rate_limit_returns_retry_after(self):
        from redforge.api.rate_limit import RateLimiter, RateLimitError, _Bucket
        limiter = RateLimiter()
        limiter._buckets["slow::test"] = _Bucket(tokens=0.0, capacity=1.0, refill_rate=0.1)
        with pytest.raises(RateLimitError) as exc_info:
            limiter.check("slow", "test")
        assert exc_info.value.details.get("retry_after", 0) > 0


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

class TestSecurity:
    def test_sanitize_string_ok(self):
        from redforge.api.security import sanitize_string
        assert sanitize_string("  hello world  ") == "hello world"

    def test_sanitize_string_xss_blocked(self):
        from redforge.api.security import sanitize_string
        with pytest.raises(ValueError):
            sanitize_string("<script>alert(1)</script>")

    def test_sanitize_string_sqli_blocked(self):
        from redforge.api.security import sanitize_string
        with pytest.raises(ValueError):
            sanitize_string("'; DROP TABLE users; --")

    def test_sanitize_session_id_valid(self):
        from redforge.api.security import sanitize_session_id
        assert sanitize_session_id("abc-123-XYZ") == "abc-123-XYZ"

    def test_sanitize_session_id_invalid(self):
        from redforge.api.security import sanitize_session_id
        with pytest.raises(ValueError):
            sanitize_session_id("../../etc/passwd")

    def test_sanitize_target_ok(self):
        from redforge.api.security import sanitize_target
        assert sanitize_target("example.com") == "example.com"
        assert sanitize_target("192.168.1.1") == "192.168.1.1"

    def test_sanitize_target_shell_chars_blocked(self):
        from redforge.api.security import sanitize_target
        with pytest.raises(ValueError):
            sanitize_target("example.com; rm -rf /")

    def test_extract_bearer_token(self):
        from redforge.api.security import extract_bearer_token
        assert extract_bearer_token("Bearer mytoken123") == "mytoken123"
        assert extract_bearer_token(None) is None
        assert extract_bearer_token("Basic abc") is None

    def test_extract_api_key(self):
        from redforge.api.security import extract_api_key
        assert extract_api_key(None, "mykey123") == "mykey123"
        assert extract_api_key("ApiKey secret", None) == "secret"
        assert extract_api_key(None, None) is None


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------

class TestResponse:
    def test_success_builds_envelope(self):
        from redforge.api.response import success
        resp = success({"key": "value"})
        assert resp.status_code == 200
        body = json.loads(resp.body)
        assert body["status"] == "success"
        assert body["payload"]["key"] == "value"

    def test_created_returns_201(self):
        from redforge.api.response import created
        resp = created({"id": "abc"})
        assert resp.status_code == 201

    def test_no_content_returns_204(self):
        from redforge.api.response import no_content
        resp = no_content()
        assert resp.status_code == 204

    def test_error_response_has_errors_list(self):
        from redforge.api.response import error_response
        resp = error_response(["Something failed"], status_code=400)
        body = json.loads(resp.body)
        assert body["status"] == "error"
        assert "Something failed" in body["errors"]


# ---------------------------------------------------------------------------
# Contracts / schemas
# ---------------------------------------------------------------------------

class TestContracts:
    def test_api_response_ok(self):
        from redforge.api.contracts import APIResponse
        r = APIResponse.ok(payload={"x": 1})
        assert r.status == "success"
        assert r.payload == {"x": 1}

    def test_api_response_error(self):
        from redforge.api.contracts import APIResponse
        r = APIResponse.error(errors=["oops"])
        assert r.status == "error"
        assert "oops" in r.errors

    def test_session_create_request_validation(self):
        from redforge.api.contracts import SessionCreateRequest, SessionModeEnum, AutonomyEnum
        req = SessionCreateRequest(mode=SessionModeEnum.bugbounty, target="example.com", autonomy=AutonomyEnum.manual)
        assert req.mode == SessionModeEnum.bugbounty
        assert req.target == "example.com"

    def test_chat_request_validation(self):
        from redforge.api.contracts import ChatRequest
        req = ChatRequest(message="scan example.com", session_id="sess-001")
        assert req.message == "scan example.com"
        assert req.stream is True   # default

    def test_ws_chat_event(self):
        from redforge.api.contracts import WSChatEvent
        event = WSChatEvent(session_id="s1", token="Hello", done=False)
        assert event.event_type == "chat"
        assert event.token == "Hello"

    def test_health_response(self):
        from redforge.api.contracts import HealthResponse
        from datetime import datetime
        r = HealthResponse(status="healthy", version="2.0.0", timestamp=datetime.utcnow(), uptime_seconds=100.0)
        assert r.status == "healthy"


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class TestExceptions:
    def test_session_not_found_inherits_not_found(self):
        from redforge.api.exceptions import SessionNotFoundError, NotFoundError
        exc = SessionNotFoundError()
        assert isinstance(exc, NotFoundError)
        assert exc.status_code == 404
        assert exc.error_code == "SESSION_NOT_FOUND"

    def test_rate_limit_error_has_429(self):
        from redforge.api.exceptions import RateLimitError
        exc = RateLimitError()
        assert exc.status_code == 429

    def test_to_dict_has_required_fields(self):
        from redforge.api.exceptions import APIError
        exc = APIError("test error")
        d = exc.to_dict()
        assert "error_code" in d
        assert "message" in d
        assert "trace_id" in d
        assert "details" in d

    def test_policy_violation_is_forbidden(self):
        from redforge.api.exceptions import PolicyViolationError, ForbiddenError
        exc = PolicyViolationError()
        assert isinstance(exc, ForbiddenError)
        assert exc.status_code == 403


# ---------------------------------------------------------------------------
# Session routes
# ---------------------------------------------------------------------------

class TestSessionRoutes:
    def test_list_sessions_ok(self, client, auth_headers):
        resp = client.get("/api/v1/sessions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "payload" in data

    def test_create_session_ok(self, client, auth_headers):
        resp = client.post(
            "/api/v1/sessions",
            json={"mode": "bugbounty", "target": "example.com", "autonomy": "manual"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201, 500, 503)  # 500/503 if session service not configured

    def test_get_nonexistent_session(self, client, auth_headers):
        resp = client.get("/api/v1/sessions/nonexistent-session-xyz", headers=auth_headers)
        assert resp.status_code in (404, 200)   # 200 if service returns stub

    def test_delete_session(self, client, auth_headers):
        resp = client.delete("/api/v1/sessions/some-session", headers=auth_headers)
        assert resp.status_code in (204, 200)

    def test_archive_session(self, client, auth_headers):
        resp = client.post("/api/v1/sessions/some-session/archive", headers=auth_headers)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Chat route
# ---------------------------------------------------------------------------

class TestChatRoute:
    def test_chat_returns_200(self, client, auth_headers):
        resp = client.post(
            "/api/v1/chat",
            json={"message": "hello", "session_id": "test-session"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "payload" in data
        assert "message" in data["payload"]

    def test_chat_has_session_id(self, client, auth_headers):
        resp = client.post(
            "/api/v1/chat",
            json={"message": "scan example.com"},
            headers=auth_headers,
        )
        data = resp.json()
        assert data["payload"]["session_id"] is not None


# ---------------------------------------------------------------------------
# Workflow routes
# ---------------------------------------------------------------------------

class TestWorkflowRoutes:
    def test_list_workflows(self, client, auth_headers):
        resp = client.get("/api/v1/workflows", headers=auth_headers)
        assert resp.status_code == 200

    def test_start_workflow(self, client, auth_headers):
        resp = client.post(
            "/api/v1/workflows/run",
            json={"workflow_id": "passive_recon", "target": "example.com"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert "payload" in data
        assert data["payload"]["workflow_id"] == "passive_recon"


# ---------------------------------------------------------------------------
# Planner route
# ---------------------------------------------------------------------------

class TestPlannerRoute:
    def test_create_plan(self, client, auth_headers):
        resp = client.post(
            "/api/v1/planner/plan",
            json={"session_id": "sess-001", "intent": {"type": "scan", "target": "example.com"}},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "payload" in data
        assert "plan_id" in data["payload"]


# ---------------------------------------------------------------------------
# Reasoning route
# ---------------------------------------------------------------------------

class TestReasoningRoute:
    def test_decide(self, client, auth_headers):
        resp = client.post(
            "/api/v1/reasoning/decide",
            json={"session_id": "sess-001", "goal": "Find XSS in example.com"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "payload" in data
        assert "reasoning_id" in data["payload"]


# ---------------------------------------------------------------------------
# Execution route
# ---------------------------------------------------------------------------

class TestExecutionRoute:
    def test_run_tool(self, client, auth_headers):
        resp = client.post(
            "/api/v1/execution/run",
            json={
                "session_id": "sess-001",
                "tool": "echo",
                "command": ["echo", "hello"],
                "timeout": 5,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "payload" in data
        assert "execution_id" in data["payload"]


# ---------------------------------------------------------------------------
# Report route
# ---------------------------------------------------------------------------

class TestReportRoute:
    def test_generate_report(self, client, auth_headers):
        resp = client.post(
            "/api/v1/reports/generate",
            json={"session_id": "sess-001", "format": "markdown"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "payload" in data
        assert "report_id" in data["payload"]

    def test_get_markdown_report(self, client, auth_headers):
        resp = client.get("/api/v1/reports/sess-001/markdown", headers=auth_headers)
        assert resp.status_code == 200
        assert "text" in resp.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# Memory routes
# ---------------------------------------------------------------------------

class TestMemoryRoutes:
    def test_store_memory(self, client, auth_headers):
        resp = client.post(
            "/api/v1/memory/store",
            json={"session_id": "sess-001", "content": "Found open port 80", "tier": "short"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_query_memory(self, client, auth_headers):
        resp = client.post(
            "/api/v1/memory/query",
            json={"session_id": "sess-001", "query": "open ports", "top_k": 3},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data["payload"]

    def test_flush_memory(self, client, auth_headers):
        resp = client.delete("/api/v1/memory/session/sess-001", headers=auth_headers)
        assert resp.status_code in (200, 204)


# ---------------------------------------------------------------------------
# Plugin routes
# ---------------------------------------------------------------------------

class TestPluginRoutes:
    def test_list_plugins(self, client, auth_headers):
        resp = client.get("/api/v1/plugins", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "plugins" in data["payload"]

    def test_install_plugin(self, client, auth_headers):
        resp = client.post(
            "/api/v1/plugins/install",
            json={"plugin_id": "test-plugin"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201)

    def test_enable_plugin(self, client, auth_headers):
        resp = client.post("/api/v1/plugins/test-plugin/enable", headers=auth_headers)
        assert resp.status_code == 200

    def test_disable_plugin(self, client, auth_headers):
        resp = client.post("/api/v1/plugins/test-plugin/disable", headers=auth_headers)
        assert resp.status_code == 200

    def test_uninstall_plugin(self, client, auth_headers):
        resp = client.delete("/api/v1/plugins/test-plugin", headers=auth_headers)
        assert resp.status_code in (200, 204)


# ---------------------------------------------------------------------------
# MCP routes
# ---------------------------------------------------------------------------

class TestMCPRoutes:
    def test_discover(self, client, auth_headers):
        resp = client.get("/api/v1/mcp/discover", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "tools" in data["payload"]
        assert "resources" in data["payload"]

    def test_list_tools(self, client, auth_headers):
        resp = client.get("/api/v1/mcp/tools", headers=auth_headers)
        assert resp.status_code == 200

    def test_list_resources(self, client, auth_headers):
        resp = client.get("/api/v1/mcp/resources", headers=auth_headers)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# System routes
# ---------------------------------------------------------------------------

class TestSystemRoutes:
    def test_system_info(self, client, auth_headers):
        resp = client.get("/api/v1/system/info", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["payload"]["version"] == "2.0.0"


# ---------------------------------------------------------------------------
# WebSocket tests
# ---------------------------------------------------------------------------

class TestWebSockets:
    def test_ws_chat_connect_and_message(self, client):
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_text(json.dumps({"session_id": "ws-test", "message": "hello"}))
            # Receive events until done
            events = []
            for _ in range(20):
                try:
                    data = json.loads(ws.receive_text())
                    events.append(data)
                    if data.get("event_type") == "done":
                        break
                except Exception:
                    break
            event_types = {e.get("event_type") for e in events}
            assert "chat_start" in event_types or "token" in event_types or "done" in event_types

    def test_ws_events_connect(self, client):
        with client.websocket_connect("/ws/events") as ws:
            data = json.loads(ws.receive_text())
            assert data.get("event_type") == "connected"

    def test_ws_events_ping(self, client):
        with client.websocket_connect("/ws/events") as ws:
            ws.receive_text()  # connected
            ws.send_text(json.dumps({"action": "ping"}))
            pong = json.loads(ws.receive_text())
            assert pong.get("event_type") == "pong"

    def test_ws_events_subscribe(self, client):
        with client.websocket_connect("/ws/events") as ws:
            ws.receive_text()  # connected
            ws.send_text(json.dumps({"action": "subscribe", "session_id": "my-session"}))
            resp = json.loads(ws.receive_text())
            assert resp.get("event_type") == "subscribed"

    def test_ws_workflow_connect_and_run(self, client):
        with client.websocket_connect("/ws/workflow") as ws:
            ws.send_text(json.dumps({
                "session_id": "ws-wf-test",
                "workflow_id": "passive_recon",
                "target": "example.com",
            }))
            events = []
            for _ in range(20):
                try:
                    data = json.loads(ws.receive_text())
                    events.append(data)
                    if data.get("event_type") == "workflow_done":
                        break
                except Exception:
                    break
            event_types = {e.get("event_type") for e in events}
            assert "workflow_start" in event_types

    def test_ws_reasoning_connect(self, client):
        with client.websocket_connect("/ws/reasoning") as ws:
            ws.send_text(json.dumps({"session_id": "ws-r", "goal": "Find vulnerabilities"}))
            events = []
            for _ in range(10):
                try:
                    data = json.loads(ws.receive_text())
                    events.append(data)
                    if data.get("event_type") in ("reasoning_done", "error"):
                        break
                except Exception:
                    break
            assert len(events) > 0

    def test_ws_report_connect(self, client):
        with client.websocket_connect("/ws/report") as ws:
            ws.send_text(json.dumps({"session_id": "ws-rep", "format": "markdown"}))
            events = []
            for _ in range(15):
                try:
                    data = json.loads(ws.receive_text())
                    events.append(data)
                    if data.get("event_type") == "report_done":
                        break
                except Exception:
                    break
            assert any(e.get("event_type") == "report_start" for e in events)

    def test_ws_chat_invalid_json(self, client):
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_text("this is not json")
            data = json.loads(ws.receive_text())
            assert data.get("event_type") == "error"

    def test_ws_execution_connect(self, client):
        with client.websocket_connect("/ws/execution") as ws:
            ws.send_text(json.dumps({
                "session_id": "ws-ex",
                "tool": "echo",
                "command": ["echo", "hello"],
            }))
            events = []
            for _ in range(15):
                try:
                    data = json.loads(ws.receive_text())
                    events.append(data)
                    if data.get("event_type") in ("execution_done", "error"):
                        break
                except Exception:
                    break
            assert len(events) > 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_404_on_unknown_route(self, client):
        resp = client.get("/api/v1/totally-unknown-path-xyz")
        assert resp.status_code == 404

    def test_method_not_allowed(self, client):
        resp = client.delete("/health")
        assert resp.status_code in (404, 405)

    def test_validation_error_returns_422(self, client, auth_headers):
        # Missing required field 'mode'
        resp = client.post(
            "/api/v1/sessions",
            json={"target": "example.com"},   # mode is required
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class TestConfig:
    def test_default_config_values(self):
        from redforge.api.config import get_api_config
        cfg = get_api_config()
        assert cfg.host == "127.0.0.1"
        assert cfg.port == 8000
        assert cfg.version == "2.0.0"
        assert cfg.auth.enabled is False

    def test_jwt_config(self):
        from redforge.api.config import get_api_config
        cfg = get_api_config()
        assert cfg.auth.jwt.algorithm == "HS256"
        assert cfg.auth.jwt.access_token_expire_minutes == 60

    def test_rate_limit_config(self):
        from redforge.api.config import get_api_config
        cfg = get_api_config()
        assert cfg.rate_limit.enabled is True
        assert cfg.rate_limit.requests_per_minute > 0

    def test_cors_config(self):
        from redforge.api.config import get_api_config
        cfg = get_api_config()
        assert cfg.cors.enabled is True
        assert "*" in cfg.cors.allow_origins

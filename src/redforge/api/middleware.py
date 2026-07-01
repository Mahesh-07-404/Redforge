"""
Middleware — Phase 16: Unified API Gateway
Request pipeline: auth injection, rate limiting, logging, timing, tracing, security headers.
"""
from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .auth import get_auth_service
from .config import get_api_config
from .exceptions import APIError, AuthenticationError, RateLimitError
from .rate_limit import get_rate_limiter
from .security import (
    SECURITY_HEADERS,
    check_content_length,
    extract_api_key,
    extract_bearer_token,
)


# ---------------------------------------------------------------------------
# Request ID / Trace ID injection
# ---------------------------------------------------------------------------

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attaches a unique request_id and trace_id to every request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        cfg = get_api_config()
        request_id = request.headers.get(cfg.request_id_header, str(uuid.uuid4()))
        trace_id = request.headers.get(cfg.trace_id_header, str(uuid.uuid4()))
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers[cfg.request_id_header] = request_id
        response.headers[cfg.trace_id_header] = trace_id
        return response


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects security headers into every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


# ---------------------------------------------------------------------------
# Request timing
# ---------------------------------------------------------------------------

class TimingMiddleware(BaseHTTPMiddleware):
    """Measures and exposes request processing time."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        cfg = get_api_config()
        start = time.perf_counter()
        response = await call_next(request)
        if cfg.include_process_time:
            elapsed_ms = (time.perf_counter() - start) * 1000
            response.headers[cfg.process_time_header] = f"{elapsed_ms:.2f}ms"
        return response


# ---------------------------------------------------------------------------
# Structured logging
# ---------------------------------------------------------------------------

class LoggingMiddleware(BaseHTTPMiddleware):
    """Structured per-request logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        cfg = get_api_config()
        if not cfg.observability.structured_logging:
            return await call_next(request)

        start = time.perf_counter()
        request_id = getattr(request.state, "request_id", "-")
        trace_id = getattr(request.state, "trace_id", "-")

        try:
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - start) * 1000
            _log_request(request, response.status_code, elapsed_ms, request_id, trace_id)
            return response
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            _log_request(request, 500, elapsed_ms, request_id, trace_id, error=str(exc))
            raise

    
def _log_request(
    request: Request,
    status_code: int,
    elapsed_ms: float,
    request_id: str,
    trace_id: str,
    error: str = "",
) -> None:
    try:
        from loguru import logger
        level = "ERROR" if status_code >= 500 else "WARNING" if status_code >= 400 else "INFO"
        logger.log(level, {
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "status": status_code,
            "duration_ms": round(elapsed_ms, 2),
            "request_id": request_id,
            "trace_id": trace_id,
            "client": (request.client.host if request.client else "unknown"),
            "error": error,
        })
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Rate limiting middleware
# ---------------------------------------------------------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP token-bucket rate limiting."""

    EXEMPT_PATHS = {"/health", "/live", "/ready", "/version"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        cfg = get_api_config()
        if not cfg.rate_limit.enabled:
            return await call_next(request)

        # Skip health probes
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        identifier = (request.client.host if request.client else "unknown")
        limiter = get_rate_limiter()
        try:
            limiter.check(identifier, endpoint=request.url.path)
        except RateLimitError as exc:
            return JSONResponse(
                status_code=429,
                content=exc.to_dict(),
                headers={"Retry-After": str(int(exc.details.get("retry_after", 60)))},
            )
        return await call_next(request)


# ---------------------------------------------------------------------------
# Authentication middleware
# ---------------------------------------------------------------------------

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Validates Bearer token or API key and attaches auth_info to request.state."""

    EXEMPT_PATHS = {
        "/health", "/live", "/ready", "/version", "/metrics",
        "/docs", "/redoc", "/openapi.json",
        "/api/v1/auth/token",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        cfg = get_api_config()
        if not cfg.auth.enabled or request.url.path in self.EXEMPT_PATHS:
            request.state.auth_info = {"authenticated": False, "scopes": ["read", "write", "execute", "report", "admin"]}
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        api_key_header = request.headers.get("X-API-Key")
        auth_service = get_auth_service()
        auth_info: dict = {}

        try:
            token = extract_bearer_token(auth_header)
            if token:
                auth_info = auth_service.verify_token(token)
                auth_info["auth_method"] = "bearer"
            else:
                raw_key = extract_api_key(auth_header, api_key_header)
                if raw_key:
                    auth_info = auth_service.verify_api_key(raw_key)
                    auth_info["auth_method"] = "api_key"
                else:
                    raise AuthenticationError("No credentials provided")
        except APIError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_dict(),
            )

        request.state.auth_info = auth_info
        return await call_next(request)


# ---------------------------------------------------------------------------
# Payload size guard middleware
# ---------------------------------------------------------------------------

class PayloadSizeMiddleware(BaseHTTPMiddleware):
    """Rejects oversized request bodies early."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        cfg = get_api_config()
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                check_content_length(int(content_length), cfg.max_request_body_bytes)
            except Exception as exc:
                return JSONResponse(status_code=413, content={"error": str(exc)})
        return await call_next(request)


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------

async def api_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    if isinstance(exc, APIError):
        exc.trace_id = trace_id
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )
    # Unexpected
    from .exceptions import InternalError
    err = InternalError(message=str(exc), trace_id=trace_id)
    return JSONResponse(status_code=500, content=err.to_dict())


# ---------------------------------------------------------------------------
# Middleware registration factory
# ---------------------------------------------------------------------------

def register_middleware(app: FastAPI) -> None:
    """Register all middleware in correct order (last-added = outermost)."""
    cfg = get_api_config()

    # CORS (outermost)
    if cfg.cors.enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cfg.cors.allow_origins,
            allow_credentials=cfg.cors.allow_credentials,
            allow_methods=cfg.cors.allow_methods,
            allow_headers=cfg.cors.allow_headers,
            max_age=cfg.cors.max_age,
        )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(PayloadSizeMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    # RequestIDMiddleware innermost so request_id is available to all others
    app.add_middleware(RequestIDMiddleware)

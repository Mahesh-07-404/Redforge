"""
API Exceptions — Phase 16: Unified API Gateway
Typed exception hierarchy with unified error responses.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import uuid4


class APIError(Exception):
    """Base class for all API-layer exceptions."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        super().__init__(message or self.message)
        self.detail_message = message or self.message
        self.details = details or {}
        self.trace_id = trace_id or str(uuid4())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.detail_message,
            "details": self.details,
            "trace_id": self.trace_id,
        }


# ---------------------------------------------------------------------------
# 4xx Client Errors
# ---------------------------------------------------------------------------

class BadRequestError(APIError):
    status_code = 400
    error_code = "BAD_REQUEST"
    message = "Invalid request."


class AuthenticationError(APIError):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"
    message = "Authentication required or credentials invalid."


class ForbiddenError(APIError):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "Access denied. Insufficient permissions."


class NotFoundError(APIError):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "The requested resource was not found."


class ConflictError(APIError):
    status_code = 409
    error_code = "CONFLICT"
    message = "Request conflicts with current state."


class UnprocessableError(APIError):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Request validation failed."


class RateLimitError(APIError):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests. Please slow down."


# ---------------------------------------------------------------------------
# 5xx Server Errors
# ---------------------------------------------------------------------------

class InternalError(APIError):
    status_code = 500
    error_code = "INTERNAL_ERROR"
    message = "An internal server error occurred."


class ServiceUnavailableError(APIError):
    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"
    message = "The service is temporarily unavailable."


class TimeoutError(APIError):
    status_code = 504
    error_code = "GATEWAY_TIMEOUT"
    message = "The operation timed out."


# ---------------------------------------------------------------------------
# Domain-specific errors
# ---------------------------------------------------------------------------

class SessionNotFoundError(NotFoundError):
    error_code = "SESSION_NOT_FOUND"
    message = "Session not found."


class SessionExpiredError(AuthenticationError):
    error_code = "SESSION_EXPIRED"
    message = "Session has expired."


class WorkflowNotFoundError(NotFoundError):
    error_code = "WORKFLOW_NOT_FOUND"
    message = "Workflow not found."


class WorkflowExecutionError(InternalError):
    error_code = "WORKFLOW_EXECUTION_ERROR"
    message = "Workflow execution failed."


class PluginNotFoundError(NotFoundError):
    error_code = "PLUGIN_NOT_FOUND"
    message = "Plugin not found."


class PluginLoadError(InternalError):
    error_code = "PLUGIN_LOAD_ERROR"
    message = "Failed to load plugin."


class ExecutionError(InternalError):
    error_code = "EXECUTION_ERROR"
    message = "Tool execution failed."


class PolicyViolationError(ForbiddenError):
    error_code = "POLICY_VIOLATION"
    message = "Request violates security policy."


class MCPError(InternalError):
    error_code = "MCP_ERROR"
    message = "MCP protocol error."


class TokenInvalidError(AuthenticationError):
    error_code = "TOKEN_INVALID"
    message = "Token is invalid or has expired."


class ApiKeyInvalidError(AuthenticationError):
    error_code = "API_KEY_INVALID"
    message = "API key is invalid or revoked."


class InsufficientScopeError(ForbiddenError):
    error_code = "INSUFFICIENT_SCOPE"
    message = "API key does not have the required scope."

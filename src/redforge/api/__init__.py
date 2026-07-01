"""
API Package — Phase 16: Unified API Gateway

Public surface:
    from redforge.api import create_app, APIConfig, APIError
"""
from .app import create_app
from .config import APIConfig, get_api_config
from .exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    ForbiddenError,
    InternalError,
    NotFoundError,
    RateLimitError,
    SessionNotFoundError,
    WorkflowNotFoundError,
)
from .server import run as run_server
from .websocket import manager as ws_manager

__all__ = [
    # App factory
    "create_app",
    "run_server",
    # Config
    "APIConfig",
    "get_api_config",
    # Exceptions
    "APIError",
    "AuthenticationError",
    "BadRequestError",
    "ForbiddenError",
    "InternalError",
    "NotFoundError",
    "RateLimitError",
    "SessionNotFoundError",
    "WorkflowNotFoundError",
    # WebSocket
    "ws_manager",
]

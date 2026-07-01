"""
API Config — Phase 16: Unified API Gateway
All API-level configuration with safe defaults.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class JWTConfig(BaseModel):
    secret_key: str = "change-me-in-production-use-32-char-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7


class RateLimitConfig(BaseModel):
    enabled: bool = True
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 20
    # Per-endpoint overrides
    chat_per_minute: int = 30
    execution_per_minute: int = 10
    report_per_minute: int = 5


class CORSConfig(BaseModel):
    enabled: bool = True
    allow_origins: list[str] = ["*"]
    allow_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    allow_headers: list[str] = ["*"]
    allow_credentials: bool = False
    max_age: int = 600


class AuthConfig(BaseModel):
    enabled: bool = False  # disabled for local single-user by default
    jwt: JWTConfig = JWTConfig()
    api_keys_enabled: bool = True
    session_tokens_enabled: bool = True
    bearer_tokens_enabled: bool = True
    rbac_enabled: bool = True


class WebSocketConfig(BaseModel):
    enabled: bool = True
    max_connections: int = 100
    ping_interval: int = 30  # seconds
    ping_timeout: int = 10
    max_message_size: int = 1_048_576  # 1 MB


class ObservabilityConfig(BaseModel):
    structured_logging: bool = True
    request_timing: bool = True
    trace_ids: bool = True
    metrics_enabled: bool = True
    log_request_body: bool = False  # sensitive data guard
    log_response_body: bool = False


class APIConfig(BaseSettings):
    """Top-level API Gateway configuration.

    Can be overridden via environment variables prefixed with REDFORGE_API_.
    Example: REDFORGE_API_HOST=0.0.0.0
    """

    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    reload: bool = False

    title: str = "RedForge API"
    description: str = "RedForge Unified API Gateway — production-grade cybersecurity AI platform"
    version: str = "2.0.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    # Sub-configs
    auth: AuthConfig = AuthConfig()
    rate_limit: RateLimitConfig = RateLimitConfig()
    cors: CORSConfig = CORSConfig()
    websocket: WebSocketConfig = WebSocketConfig()
    observability: ObservabilityConfig = ObservabilityConfig()

    # Request pipeline
    request_id_header: str = "X-Request-ID"
    trace_id_header: str = "X-Trace-ID"
    max_request_body_bytes: int = 10_485_760  # 10 MB

    # Response
    include_process_time: bool = True
    process_time_header: str = "X-Process-Time"

    class Config:
        env_prefix = "REDFORGE_API_"
        env_nested_delimiter = "__"


# Singleton
_api_config: APIConfig | None = None


def get_api_config() -> APIConfig:
    global _api_config
    if _api_config is None:
        _api_config = APIConfig()
    return _api_config

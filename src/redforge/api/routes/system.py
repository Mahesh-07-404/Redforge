"""
System routes — Phase 16: Unified API Gateway
Auth endpoints, API key management, system info.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_auth_service
from ..contracts import (
    APIKeyRequest,
    APIKeyResponse,
    TokenRequest,
    TokenResponse,
)
from ..dependencies import (
    AdminAuth,
    ReadAuth,
    get_current_auth,
    get_request_id,
    get_timer,
)
from ..exceptions import AuthenticationError
from ..response import created, no_content, success

router = APIRouter(prefix="/system", tags=["System"])


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/token", summary="Issue a JWT access token")
async def issue_token(
    body: TokenRequest, request_id: str = Depends(get_request_id), timer=Depends(get_timer)
):
    """
    Issue a JWT access token.
    In production, validate credentials against a user store.
    Currently returns a token for any non-empty credentials.
    """
    if not body.username or not body.password:
        raise AuthenticationError("Username and password are required")
    auth = get_auth_service()
    token = auth.create_token(subject=body.username)
    payload = TokenResponse(access_token=token, token_type="bearer")
    return success(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)


@auth_router.post("/api-keys", status_code=201, summary="Create an API key")
async def create_api_key(
    body: APIKeyRequest,
    auth_info=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
    timer=Depends(get_timer),
):
    """Create a new API key (admin scope required)."""
    auth = get_auth_service()
    record = auth.create_api_key(
        name=body.name,
        scopes=body.scopes,
        expires_days=body.expires_days,
    )
    payload = APIKeyResponse(
        key_id=record["key_id"],
        api_key=record["api_key"],
        name=record["name"],
        scopes=record["scopes"],
    )
    return created(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)


@auth_router.get("/api-keys", summary="List API keys")
async def list_api_keys(
    auth_info: AdminAuth, request_id: str = Depends(get_request_id), timer=Depends(get_timer)
):
    """List all API keys (admin only, API key values are not returned)."""
    auth = get_auth_service()
    keys = auth.list_api_keys()
    return success(
        {"api_keys": keys, "total": len(keys)}, duration_ms=timer.elapsed_ms, request_id=request_id
    )


@auth_router.delete("/api-keys/{key_id}", status_code=204, summary="Revoke an API key")
async def revoke_api_key(key_id: str, auth_info=Depends(get_current_auth)):
    """Revoke (disable) an API key."""
    auth = get_auth_service()
    auth.revoke_api_key(key_id)
    return no_content()


# ---------------------------------------------------------------------------
# System info
# ---------------------------------------------------------------------------


@router.get("/info", summary="System information")
async def system_info(
    auth: ReadAuth, request_id: str = Depends(get_request_id), timer=Depends(get_timer)
):
    """Return runtime and configuration metadata."""
    import platform
    import sys

    from ..config import get_api_config

    cfg = get_api_config()
    return success(
        {
            "version": "2.0.0",
            "phase": "Phase 16 — Unified API Gateway",
            "python": sys.version,
            "platform": platform.platform(),
            "auth_enabled": cfg.auth.enabled,
            "rate_limit_enabled": cfg.rate_limit.enabled,
            "websocket_enabled": cfg.websocket.enabled,
        },
        duration_ms=timer.elapsed_ms,
        request_id=request_id,
    )

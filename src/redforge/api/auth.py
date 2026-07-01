"""
Authentication & Security — Phase 16: Unified API Gateway
JWT, API Keys, Bearer Tokens, RBAC.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from uuid import uuid4

from .config import get_api_config
from .exceptions import (
    ApiKeyInvalidError,
    InsufficientScopeError,
    TokenInvalidError,
)


# ---------------------------------------------------------------------------
# RBAC roles / permissions
# ---------------------------------------------------------------------------

class Role:
    ADMIN = "admin"
    ANALYST = "analyst"
    OPERATOR = "operator"
    VIEWER = "viewer"


ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    Role.ADMIN: {
        "read", "write", "execute", "report",
        "admin", "plugin", "mcp", "session",
    },
    Role.OPERATOR: {
        "read", "write", "execute", "report", "session",
    },
    Role.ANALYST: {
        "read", "report", "session",
    },
    Role.VIEWER: {
        "read",
    },
}


# ---------------------------------------------------------------------------
# Token store (in-memory; production should use Redis/DB)
# ---------------------------------------------------------------------------

class _TokenStore:
    """Thread-safe in-memory token registry."""

    def __init__(self) -> None:
        self._tokens: Dict[str, Dict] = {}
        self._api_keys: Dict[str, Dict] = {}

    # --- JWT-style tokens (signed with HMAC-SHA256) -------------------------

    def create_access_token(
        self,
        subject: str,
        roles: List[str],
        scopes: List[str],
        expires_minutes: Optional[int] = None,
    ) -> str:
        config = get_api_config()
        exp = expires_minutes or config.auth.jwt.access_token_expire_minutes
        token_id = str(uuid4())
        expires_at = time.time() + exp * 60
        payload = {
            "sub": subject,
            "jti": token_id,
            "roles": roles,
            "scopes": scopes,
            "exp": expires_at,
        }
        self._tokens[token_id] = payload
        # Create a simple signed token: base64(payload) + "." + HMAC
        import base64, json
        encoded = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode()
        secret = config.auth.jwt.secret_key.encode()
        sig = hmac.new(secret, encoded.encode(), hashlib.sha256).hexdigest()
        return f"{encoded}.{sig}"

    def verify_token(self, token: str) -> Dict:
        import base64, json
        try:
            encoded, sig = token.rsplit(".", 1)
            config = get_api_config()
            secret = config.auth.jwt.secret_key.encode()
            expected = hmac.new(secret, encoded.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected):
                raise TokenInvalidError("Signature mismatch")
            payload = json.loads(base64.urlsafe_b64decode(encoded + "=="))
            if payload["exp"] < time.time():
                raise TokenInvalidError("Token has expired")
            token_id = payload["jti"]
            if token_id not in self._tokens:
                raise TokenInvalidError("Token has been revoked")
            return payload
        except TokenInvalidError:
            raise
        except Exception as exc:
            raise TokenInvalidError(f"Token parse error: {exc}") from exc

    def revoke_token(self, token: str) -> None:
        try:
            payload = self.verify_token(token)
            self._tokens.pop(payload["jti"], None)
        except TokenInvalidError:
            pass

    # --- API Keys -----------------------------------------------------------

    def create_api_key(
        self,
        name: str,
        scopes: List[str],
        expires_days: Optional[int] = None,
    ) -> Dict:
        key_id = str(uuid4())
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        record = {
            "key_id": key_id,
            "name": name,
            "key_hash": key_hash,
            "scopes": scopes,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (
                (datetime.utcnow() + timedelta(days=expires_days)).isoformat()
                if expires_days else None
            ),
            "enabled": True,
        }
        self._api_keys[key_hash] = record
        return {**record, "api_key": raw_key}

    def verify_api_key(self, raw_key: str) -> Dict:
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        record = self._api_keys.get(key_hash)
        if not record or not record["enabled"]:
            raise ApiKeyInvalidError()
        if record["expires_at"]:
            if datetime.fromisoformat(record["expires_at"]) < datetime.utcnow():
                raise ApiKeyInvalidError("API key has expired")
        return record

    def revoke_api_key(self, key_id: str) -> None:
        for record in self._api_keys.values():
            if record["key_id"] == key_id:
                record["enabled"] = False
                return

    def list_api_keys(self) -> List[Dict]:
        return [
            {k: v for k, v in r.items() if k != "key_hash"}
            for r in self._api_keys.values()
        ]


_store = _TokenStore()


# ---------------------------------------------------------------------------
# Auth facade
# ---------------------------------------------------------------------------

class AuthService:
    """Provides all authentication and authorization operations."""

    def create_token(
        self,
        subject: str = "system",
        roles: Optional[List[str]] = None,
        scopes: Optional[List[str]] = None,
        expires_minutes: Optional[int] = None,
    ) -> str:
        return _store.create_access_token(
            subject=subject,
            roles=roles or [Role.OPERATOR],
            scopes=scopes or list(ROLE_PERMISSIONS[Role.OPERATOR]),
            expires_minutes=expires_minutes,
        )

    def verify_token(self, token: str) -> Dict:
        return _store.verify_token(token)

    def revoke_token(self, token: str) -> None:
        _store.revoke_token(token)

    def create_api_key(
        self,
        name: str,
        scopes: Optional[List[str]] = None,
        expires_days: Optional[int] = None,
    ) -> Dict:
        return _store.create_api_key(
            name=name,
            scopes=scopes or ["read", "write"],
            expires_days=expires_days,
        )

    def verify_api_key(self, raw_key: str) -> Dict:
        return _store.verify_api_key(raw_key)

    def revoke_api_key(self, key_id: str) -> None:
        _store.revoke_api_key(key_id)

    def list_api_keys(self) -> List[Dict]:
        return _store.list_api_keys()

    def check_scope(self, auth_info: Dict, required_scope: str) -> None:
        """Raise InsufficientScopeError if auth_info lacks required_scope."""
        config = get_api_config()
        if not config.auth.enabled:
            return
        scopes: List[str] = auth_info.get("scopes", [])
        if "admin" in scopes:
            return
        if required_scope not in scopes:
            raise InsufficientScopeError(
                f"Required scope '{required_scope}' not granted"
            )

    def check_role(self, auth_info: Dict, required_role: str) -> None:
        """Raise ForbiddenError if auth_info lacks required_role."""
        config = get_api_config()
        if not config.auth.enabled:
            return
        roles: List[str] = auth_info.get("roles", [])
        if Role.ADMIN in roles or required_role in roles:
            return
        from .exceptions import ForbiddenError
        raise ForbiddenError(f"Required role '{required_role}' not granted")


# Singleton
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service

"""
Security Middleware helpers — Phase 16: Unified API Gateway
Input sanitization, header security, payload size guard.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Input sanitization
# ---------------------------------------------------------------------------

# Patterns that are never valid in API inputs
_DANGEROUS_PATTERNS = [
    re.compile(r"<script[^>]*>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),  # onerror=, onclick=, …
    re.compile(r";\s*DROP\s+TABLE", re.IGNORECASE),
    re.compile(r"UNION\s+SELECT", re.IGNORECASE),
]


def sanitize_string(value: str, max_length: int = 4096) -> str:
    """Strip leading/trailing whitespace, enforce max_length, reject XSS/SQLi."""
    value = value.strip()
    if len(value) > max_length:
        value = value[:max_length]
    for pattern in _DANGEROUS_PATTERNS:
        if pattern.search(value):
            raise ValueError(f"Input contains forbidden pattern: {pattern.pattern!r}")
    return value


def sanitize_session_id(value: str) -> str:
    """Session IDs must be alphanumeric + hyphens only."""
    if not re.fullmatch(r"[a-zA-Z0-9\-]{1,64}", value):
        raise ValueError(f"Invalid session_id format: {value!r}")
    return value


def sanitize_target(target: str | None) -> str | None:
    """Allow domains, IPs, URLs; block anything with shell meta-chars."""
    if target is None:
        return None
    target = target.strip()
    if re.search(r"[;&|`$(){}]", target):
        raise ValueError(f"Target contains shell meta-characters: {target!r}")
    return target


# ---------------------------------------------------------------------------
# Security response headers
# ---------------------------------------------------------------------------

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


# ---------------------------------------------------------------------------
# Payload size guard
# ---------------------------------------------------------------------------


def check_content_length(content_length: int | None, limit_bytes: int) -> None:
    if content_length is not None and content_length > limit_bytes:
        from .exceptions import BadRequestError

        raise BadRequestError(
            f"Request body too large: {content_length} bytes (limit {limit_bytes})"
        )


# ---------------------------------------------------------------------------
# Bearer token extraction
# ---------------------------------------------------------------------------


def extract_bearer_token(authorization: str | None) -> str | None:
    """Parse 'Bearer <token>' header, returning the raw token or None."""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def extract_api_key(authorization: str | None, header_value: str | None) -> str | None:
    """Check Authorization header for ApiKey scheme, or dedicated X-API-Key header."""
    if header_value:
        return header_value.strip()
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() in ("apikey", "api-key"):
        return parts[1]
    return None

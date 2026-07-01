"""
Rate Limiter — Phase 16: Unified API Gateway
Token-bucket per-IP + per-key rate limiting with burst support.
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from .config import get_api_config
from .exceptions import RateLimitError


@dataclass
class _Bucket:
    """Token-bucket state for one (key, endpoint) pair."""
    tokens: float
    capacity: float
    refill_rate: float          # tokens per second
    last_refill: float = field(default_factory=time.monotonic)

    def consume(self, amount: float = 1.0) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False

    @property
    def retry_after(self) -> float:
        """Seconds until at least 1 token is available."""
        if self.tokens >= 1.0:
            return 0.0
        return (1.0 - self.tokens) / self.refill_rate


class RateLimiter:
    """
    In-memory token-bucket rate limiter.

    Production note: swap self._buckets for a Redis backend to support
    multi-process / multi-node deployments.
    """

    def __init__(self) -> None:
        # key -> Bucket
        self._buckets: Dict[str, _Bucket] = defaultdict(lambda: _Bucket(0, 0, 0))

    def _bucket_key(self, identifier: str, endpoint: str) -> str:
        return f"{identifier}::{endpoint}"

    def _make_bucket(self, endpoint: str) -> _Bucket:
        cfg = get_api_config().rate_limit
        # Endpoint-specific overrides
        per_minute = cfg.requests_per_minute
        burst = cfg.burst_size
        if "chat" in endpoint:
            per_minute = cfg.chat_per_minute
            burst = min(burst, 10)
        elif "execution" in endpoint:
            per_minute = cfg.execution_per_minute
            burst = min(burst, 5)
        elif "report" in endpoint:
            per_minute = cfg.report_per_minute
            burst = min(burst, 3)
        refill_rate = per_minute / 60.0
        return _Bucket(tokens=float(burst), capacity=float(burst), refill_rate=refill_rate)

    def check(self, identifier: str, endpoint: str = "default") -> Tuple[bool, float]:
        """
        Returns (allowed, retry_after_seconds).
        Raises RateLimitError if denied.
        """
        cfg = get_api_config().rate_limit
        if not cfg.enabled:
            return True, 0.0

        key = self._bucket_key(identifier, endpoint)
        if key not in self._buckets:
            self._buckets[key] = self._make_bucket(endpoint)

        bucket = self._buckets[key]
        if bucket.consume():
            return True, 0.0
        retry_after = bucket.retry_after
        raise RateLimitError(
            message=f"Rate limit exceeded. Retry after {retry_after:.1f}s",
            details={"retry_after": retry_after, "endpoint": endpoint},
        )

    def reset(self, identifier: str, endpoint: str = "default") -> None:
        """Reset bucket for testing or admin override."""
        key = self._bucket_key(identifier, endpoint)
        self._buckets.pop(key, None)

    def get_status(self, identifier: str, endpoint: str = "default") -> Dict:
        key = self._bucket_key(identifier, endpoint)
        if key not in self._buckets:
            return {"tokens": "N/A", "capacity": "N/A"}
        b = self._buckets[key]
        return {
            "tokens": round(b.tokens, 2),
            "capacity": b.capacity,
            "refill_rate_per_s": round(b.refill_rate, 4),
        }


# Singleton
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

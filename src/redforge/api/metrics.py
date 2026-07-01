"""
Metrics — Phase 16: Unified API Gateway
Prometheus-compatible metrics exposition.
"""

from __future__ import annotations

from .routes.health import _metrics, increment

__all__ = ["_metrics", "increment"]

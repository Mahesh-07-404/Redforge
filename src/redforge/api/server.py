"""
API Server — Phase 16: Unified API Gateway
Entry point for running the server with uvicorn.
"""
from __future__ import annotations

import signal
import sys
from typing import Optional

from .app import create_app
from .config import get_api_config


def run(
    host: Optional[str] = None,
    port: Optional[int] = None,
    reload: bool = False,
    log_level: str = "info",
) -> None:
    """Start the RedForge API server."""
    try:
        import uvicorn
    except ImportError:
        print(
            "uvicorn is required to run the API server.\n"
            "Install with: pip install 'redforge[web]'",
            file=sys.stderr,
        )
        sys.exit(1)

    cfg = get_api_config()
    _host = host or cfg.host
    _port = port or cfg.port

    app = create_app()

    print(f"""
╔══════════════════════════════════════════════════════╗
║         RedForge API Gateway — v2.0.0                ║
║         Phase 16: Unified API Gateway                ║
╠══════════════════════════════════════════════════════╣
║  Host:    http://{_host}:{_port:<36}║
║  Docs:    http://{_host}:{_port}/docs{' ' * 30}║
║  ReDoc:   http://{_host}:{_port}/redoc{' ' * 29}║
║  OpenAPI: http://{_host}:{_port}/openapi.json{' ' * 22}║
╚══════════════════════════════════════════════════════╝
    """.strip())

    uvicorn.run(
        app,
        host=_host,
        port=_port,
        reload=cfg.reload or reload,
        log_level=log_level,
        access_log=cfg.observability.structured_logging,
    )


if __name__ == "__main__":
    run()

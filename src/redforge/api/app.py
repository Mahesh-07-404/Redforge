"""
FastAPI Application Factory — Phase 16: Unified API Gateway
"""

from __future__ import annotations

from fastapi import FastAPI

from .config import get_api_config
from .exceptions import APIError
from .middleware import api_exception_handler, register_middleware
from .websocket import router as ws_router


def create_app() -> FastAPI:
    """
    Factory function.  Returns a fully configured FastAPI application.

    Usage:
        app = create_app()
        uvicorn.run(app, host="127.0.0.1", port=8000)
    """
    cfg = get_api_config()

    app = FastAPI(
        title=cfg.title,
        description=cfg.description,
        version=cfg.version,
        docs_url=cfg.docs_url,
        redoc_url=cfg.redoc_url,
        openapi_url=cfg.openapi_url,
        # Disable default exception handlers — ours are more structured
        generate_unique_id_function=lambda route: route.name,
    )

    # ---- Middleware (outermost → innermost) --------------------------------
    register_middleware(app)

    # ---- Exception handlers ------------------------------------------------
    app.add_exception_handler(APIError, api_exception_handler)
    app.add_exception_handler(Exception, api_exception_handler)

    # ---- Routers -----------------------------------------------------------
    _register_routes(app)

    # ---- WebSocket routes --------------------------------------------------
    app.include_router(ws_router)

    # ---- Custom OpenAPI schema --------------------------------------------
    app.openapi_schema = None  # reset so it regenerates with our schema

    return app


def _register_routes(app: FastAPI) -> None:
    """Register all REST route prefixes under /api/v1."""
    from .routes import (
        auth_router,
        conversation_router,
        execution_router,
        health_router,
        mcp_router,
        memory_router,
        planner_router,
        plugins_router,
        reasoning_router,
        report_router,
        sessions_router,
        system_router,
        workflow_router,
    )

    v1 = "/api/v1"

    # Health probes (also available at root level)
    app.include_router(health_router)  # /health /ready /live /version /metrics

    # Versioned REST API
    app.include_router(sessions_router, prefix=v1)  # /api/v1/sessions/…
    app.include_router(conversation_router, prefix=v1)  # /api/v1/chat  /api/v1/conversations/…
    app.include_router(workflow_router, prefix=v1)  # /api/v1/workflows/…
    app.include_router(planner_router, prefix=v1)  # /api/v1/planner/…
    app.include_router(reasoning_router, prefix=v1)  # /api/v1/reasoning/…
    app.include_router(execution_router, prefix=v1)  # /api/v1/execution/…
    app.include_router(report_router, prefix=v1)  # /api/v1/reports/…
    app.include_router(memory_router, prefix=v1)  # /api/v1/memory/…
    app.include_router(plugins_router, prefix=v1)  # /api/v1/plugins/…
    app.include_router(mcp_router, prefix=v1)  # /api/v1/mcp/…
    app.include_router(system_router, prefix=v1)  # /api/v1/system/…
    app.include_router(auth_router, prefix=v1)  # /api/v1/auth/…

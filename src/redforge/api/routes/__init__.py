"""
Routes package init — Phase 16: Unified API Gateway
"""
from .health import router as health_router
from .sessions import router as sessions_router
from .conversation import router as conversation_router
from .workflow import router as workflow_router
from .planner import router as planner_router
from .reasoning import router as reasoning_router
from .execution import router as execution_router
from .report import router as report_router
from .memory import router as memory_router
from .plugins import router as plugins_router
from .mcp import router as mcp_router
from .system import router as system_router, auth_router

__all__ = [
    "health_router",
    "sessions_router",
    "conversation_router",
    "workflow_router",
    "planner_router",
    "reasoning_router",
    "execution_router",
    "report_router",
    "memory_router",
    "plugins_router",
    "mcp_router",
    "system_router",
    "auth_router",
]

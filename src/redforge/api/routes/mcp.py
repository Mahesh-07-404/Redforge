"""
MCP routes — Phase 16: Unified API Gateway
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..contracts import MCPDiscoveryResponse, MCPToolResponse, MCPResourceResponse
from ..dependencies import get_current_auth, get_request_id, get_timer, ReadAuth
from ..response import success

router = APIRouter(prefix="/mcp", tags=["MCP (Model Context Protocol)"])


@router.get("/discover", summary="Discover all MCP tools and resources")
async def discover(auth: ReadAuth, request_id: str = Depends(get_request_id), timer=Depends(get_timer)):
    """Return all registered MCP tools and resources."""
    tools: list = []
    resources: list = []

    try:
        from redforge.mcp.registry import MCPRegistry
        registry = MCPRegistry()
        raw_tools = registry.list_tools() if hasattr(registry, "list_tools") else []
        raw_resources = registry.list_resources() if hasattr(registry, "list_resources") else []
        for t in raw_tools:
            tools.append(t if isinstance(t, dict) else vars(t))
        for r in raw_resources:
            resources.append(r if isinstance(r, dict) else vars(r))
    except Exception:
        pass

    payload = MCPDiscoveryResponse(
        tools=[MCPToolResponse(**t) for t in tools],
        resources=[MCPResourceResponse(**r) for r in resources],
        server_version="2.0.0",
    )
    return success(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)


@router.get("/tools", summary="List available MCP tools")
async def list_tools(auth: ReadAuth, request_id: str = Depends(get_request_id), timer=Depends(get_timer)):
    tools: list = []
    try:
        from redforge.mcp.registry import MCPRegistry
        registry = MCPRegistry()
        raw_tools = registry.list_tools() if hasattr(registry, "list_tools") else []
        tools = [t if isinstance(t, dict) else vars(t) for t in raw_tools]
    except Exception:
        pass
    return success({"tools": tools, "total": len(tools)}, duration_ms=timer.elapsed_ms, request_id=request_id)


@router.get("/resources", summary="List available MCP resources")
async def list_resources(auth: ReadAuth, request_id: str = Depends(get_request_id), timer=Depends(get_timer)):
    resources: list = []
    try:
        from redforge.mcp.registry import MCPRegistry
        registry = MCPRegistry()
        raw = registry.list_resources() if hasattr(registry, "list_resources") else []
        resources = [r if isinstance(r, dict) else vars(r) for r in raw]
    except Exception:
        pass
    return success({"resources": resources, "total": len(resources)}, duration_ms=timer.elapsed_ms, request_id=request_id)

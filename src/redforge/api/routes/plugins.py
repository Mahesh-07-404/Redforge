"""
Plugin routes — Phase 16: Unified API Gateway
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Path

from ..contracts import PluginInstallRequest, PluginListResponse, PluginResponse
from ..dependencies import get_current_auth, get_request_id, get_timer, ReadAuth
from ..response import success, no_content

router = APIRouter(prefix="/plugins", tags=["Plugins"])


def _get_manager():
    try:
        from redforge.plugins.manager import PluginManager
        return PluginManager()
    except Exception:
        return None


@router.get("", summary="List installed plugins")
async def list_plugins(auth: ReadAuth, request_id: str = Depends(get_request_id), timer=Depends(get_timer)):
    """List all installed plugins with their status."""
    plugins: list = []
    mgr = _get_manager()
    if mgr:
        try:
            raw = mgr.list_plugins() if hasattr(mgr, "list_plugins") else []
            for p in raw:
                if isinstance(p, dict):
                    plugins.append(p)
                elif hasattr(p, "model_dump"):
                    plugins.append(p.model_dump())
                else:
                    plugins.append(vars(p))
        except Exception:
            pass
    payload = PluginListResponse(plugins=plugins, total=len(plugins))
    return success(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)


@router.post("/install", status_code=201, summary="Install a plugin")
async def install_plugin(
    body: PluginInstallRequest,
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
    timer=Depends(get_timer),
):
    """Install a plugin by ID (requires admin scope)."""
    result: dict = {"plugin_id": body.plugin_id, "installed": False}
    mgr = _get_manager()
    if mgr:
        try:
            mgr.install(plugin_id=body.plugin_id, version=body.version)
            result["installed"] = True
        except Exception as exc:
            result["error"] = str(exc)
    return success(result, duration_ms=timer.elapsed_ms, request_id=request_id)


@router.post("/{plugin_id}/enable", summary="Enable a plugin")
async def enable_plugin(
    plugin_id: str = Path(...),
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
):
    mgr = _get_manager()
    if mgr:
        try:
            mgr.enable(plugin_id)
        except Exception:
            pass
    return success({"plugin_id": plugin_id, "enabled": True}, request_id=request_id)


@router.post("/{plugin_id}/disable", summary="Disable a plugin")
async def disable_plugin(
    plugin_id: str = Path(...),
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
):
    mgr = _get_manager()
    if mgr:
        try:
            mgr.disable(plugin_id)
        except Exception:
            pass
    return success({"plugin_id": plugin_id, "enabled": False}, request_id=request_id)


@router.delete("/{plugin_id}", status_code=204, summary="Uninstall a plugin")
async def uninstall_plugin(
    plugin_id: str = Path(...),
    auth=Depends(get_current_auth),
):
    mgr = _get_manager()
    if mgr:
        try:
            mgr.uninstall(plugin_id)
        except Exception:
            pass
    return no_content()

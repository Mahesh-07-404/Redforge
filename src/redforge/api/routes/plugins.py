"""
Plugin routes — Phase 16: Unified API Gateway
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Path

from ..contracts import PluginInstallRequest, PluginListResponse
from ..dependencies import AuthInfo, ReadAuth, RequestID, Timer
from ..response import no_content, success

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["Plugins"])


def _get_manager():
    try:
        from redforge.plugins.manager import PluginManager

        return PluginManager()
    except Exception as exc:  # nosec B110 - plugin manager failure is handled by returning None
        logger.debug("Failed to load PluginManager: %s", exc)
        return None


@router.get("", summary="List installed plugins")
async def list_plugins(auth: ReadAuth, request_id: RequestID, timer: Timer):
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
        except Exception as exc:  # nosec B110 - listing plugins is best-effort
            logger.warning("Failed to list plugins: %s", exc)
    payload = PluginListResponse(plugins=plugins, total=len(plugins))
    return success(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)


@router.post("/install", status_code=201, summary="Install a plugin")
async def install_plugin(
    body: PluginInstallRequest,
    auth: AuthInfo,
    request_id: RequestID,
    timer: Timer,
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
    auth: AuthInfo,
    request_id: RequestID,
    plugin_id: str = Path(...),
):
    mgr = _get_manager()
    if mgr:
        try:
            mgr.enable(plugin_id)
        except Exception as exc:  # nosec B110 - enabling plugin is best-effort
            logger.warning("Failed to enable plugin '%s': %s", plugin_id, exc)
    return success({"plugin_id": plugin_id, "enabled": True}, request_id=request_id)


@router.post("/{plugin_id}/disable", summary="Disable a plugin")
async def disable_plugin(
    auth: AuthInfo,
    request_id: RequestID,
    plugin_id: str = Path(...),
):
    mgr = _get_manager()
    if mgr:
        try:
            mgr.disable(plugin_id)
        except Exception as exc:  # nosec B110 - disabling plugin is best-effort
            logger.warning("Failed to disable plugin '%s': %s", plugin_id, exc)
    return success({"plugin_id": plugin_id, "enabled": False}, request_id=request_id)


@router.delete("/{plugin_id}", status_code=204, summary="Uninstall a plugin")
async def uninstall_plugin(
    auth: AuthInfo,
    plugin_id: str = Path(...),
):
    mgr = _get_manager()
    if mgr:
        try:
            mgr.uninstall(plugin_id)
        except Exception as exc:  # nosec B110 - uninstalling plugin is best-effort
            logger.warning("Failed to uninstall plugin '%s': %s", plugin_id, exc)
    return no_content()

from .contracts import PluginMetadata
from .events import PluginEvents
from .exceptions import PluginError, PluginLoadError, PluginValidationError
from .hooks import PluginHooks

# Legacy bug bounty platform integrations for backwards compatibility
from .legacy import (
    BasePlatform,
    BugcrowdAPI,
    HackerOneAPI,
    Platform,
    PlatformManager,
    Program,
    Report,
    Submission,
    create_submission,
)
from .loader import PluginLoader
from .manager import PluginManager
from .permissions import PluginPermissionManager
from .registry import PluginRegistry
from .sandbox import PluginSandbox

__all__ = [
    "PluginMetadata",
    "PluginError",
    "PluginLoadError",
    "PluginValidationError",
    "PluginPermissionManager",
    "PluginSandbox",
    "PluginHooks",
    "PluginEvents",
    "PluginRegistry",
    "PluginLoader",
    "PluginManager",
    # Legacy exports
    "Platform",
    "Program",
    "Submission",
    "Report",
    "BasePlatform",
    "HackerOneAPI",
    "BugcrowdAPI",
    "PlatformManager",
    "create_submission",
]

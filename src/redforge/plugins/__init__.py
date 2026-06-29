from .contracts import PluginMetadata
from .exceptions import PluginError, PluginLoadError, PluginValidationError
from .permissions import PluginPermissionManager
from .sandbox import PluginSandbox
from .hooks import PluginHooks
from .events import PluginEvents
from .registry import PluginRegistry
from .loader import PluginLoader
from .manager import PluginManager

# Legacy bug bounty platform integrations for backwards compatibility
from .legacy import (
    Platform,
    Program,
    Submission,
    Report,
    BasePlatform,
    HackerOneAPI,
    BugcrowdAPI,
    PlatformManager,
    create_submission
)

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
    "create_submission"
]

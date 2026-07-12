class PluginError(Exception):
    """Base exception for plugins"""

    pass


class PluginLoadError(PluginError):
    """Raised when plugin loading fails"""

    pass


class PluginValidationError(PluginError):
    """Raised when plugin validation fails"""

    pass

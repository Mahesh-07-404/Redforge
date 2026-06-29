class ToolRegistryError(Exception):
    """Base exception for tool registry operations"""
    pass

class ToolNotFoundError(ToolRegistryError):
    """Raised when a requested tool cannot be found"""
    pass

class UnsupportedPlatformError(ToolRegistryError):
    """Raised when a tool is not supported on the current platform"""
    pass

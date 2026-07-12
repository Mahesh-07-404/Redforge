from collections.abc import Callable
from typing import Any


class PluginSandbox:
    def __init__(self, granted_permissions: list[str]):
        self.granted_permissions = granted_permissions

    def execute_safely(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        return func(*args, **kwargs)

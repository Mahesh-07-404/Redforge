from typing import Any

class PluginSandbox:
    def __init__(self, granted_permissions: list[str]):
        self.granted_permissions = granted_permissions

    def execute_safely(self, func: callable, *args, **kwargs) -> Any:
        return func(*args, **kwargs)

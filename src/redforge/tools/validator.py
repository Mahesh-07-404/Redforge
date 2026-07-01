from .discovery import ToolDiscovery
from .platform import detect_platform
from .tool import Tool


class ToolValidator:
    def validate(self, tool: Tool) -> list[str]:
        errors = []

        # 1. binary exists
        binary_path = ToolDiscovery.find_binary(tool.binary)
        if not binary_path:
            errors.append(f"Binary '{tool.binary}' not found on PATH or default paths.")

        # 2. supported platform
        plat = detect_platform()
        if tool.platforms and plat.name not in tool.platforms:
            errors.append(f"Platform '{plat.name}' not supported by tool '{tool.name}'.")

        return errors

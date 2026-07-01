from .tool import Tool
from .platform import detect_platform

class ToolInstaller:
    """Only generates installation plans. Never executes them."""
    def is_installed(self, tool_name: str) -> bool:
        from .registry import ToolRegistry
        from .discovery import ToolDiscovery
        try:
            tool = ToolRegistry().lookup_tool_by_name(tool_name)
            return ToolDiscovery.find_binary(tool.binary) is not None
        except Exception:
            return ToolDiscovery.find_binary(tool_name) is not None

    def generate_install_plan(self, tool: Tool) -> dict:
        plat = detect_platform()
        pkg = tool.package or tool.binary
        
        # Determine install command based on package manager
        if plat.package_manager == "pacman":
            cmd = f"sudo pacman -S --noconfirm {pkg}"
        elif plat.package_manager == "dnf":
            cmd = f"sudo dnf install -y {pkg}"
        elif plat.package_manager == "brew":
            cmd = f"brew install {pkg}"
        elif plat.package_manager == "choco":
            cmd = f"choco install -y {pkg}"
        else:
            cmd = f"sudo apt install -y {pkg}"
            
        if tool.install_command:
            cmd = tool.install_command
            
        return {
            "tool_id": tool.id,
            "tool_name": tool.name,
            "platform": plat.name,
            "package_manager": plat.package_manager,
            "install_command": cmd,
            "steps": [
                f"Identify package manager: {plat.package_manager}",
                f"Verify platform requirements for {plat.name}",
                f"Execute command: {cmd}"
            ]
        }

from .exceptions import ToolRegistryError, ToolNotFoundError, UnsupportedPlatformError
from .capabilities import Capability
from .platform import PlatformInfo, detect_platform
from .tool import Tool
from .discovery import ToolDiscovery
from .validator import ToolValidator
from .installer import ToolInstaller
from .registry import ToolRegistry
from .resolver import ToolResolver

from enum import Enum
from typing import Optional, List, Dict
from dataclasses import dataclass, field
import shutil
import platform
import logging

logger = logging.getLogger(__name__)

class Platform(Enum):
    KALI = "kali"
    DEBIAN = "debian"
    UBUNTU = "ubuntu"
    ARCH = "arch"
    FEDORA = "fedora"
    MACOS = "macos"
    WINDOWS = "windows"

@dataclass
class ToolStatus:
    name: str
    installed: bool
    version: Optional[str] = None
    path: Optional[str] = None
    auto_install: bool = True

class PlatformDetector:
    @staticmethod
    def detect() -> Platform:
        system = platform.system().lower()
        if system == "windows":
            return Platform.WINDOWS
        elif system == "darwin":
            return Platform.MACOS
        elif system == "linux":
            try:
                with open("/etc/os-release") as f:
                    content = f.read().lower()
                    if "kali" in content:
                        return Platform.KALI
                    elif "arch" in content:
                        return Platform.ARCH
                    elif "fedora" in content:
                        return Platform.FEDORA
                    elif "ubuntu" in content:
                        return Platform.UBUNTU
                    else:
                        return Platform.DEBIAN
            except:
                return Platform.DEBIAN
        return Platform.DEBIAN

    @staticmethod
    def get_package_manager() -> str:
        p = PlatformDetector.detect()
        if p == Platform.ARCH:
            return "pacman"
        elif p == Platform.FEDORA:
            return "dnf"
        elif p in (Platform.KALI, Platform.DEBIAN, Platform.UBUNTU):
            return "apt"
        elif p == Platform.MACOS:
            return "brew"
        elif p == Platform.WINDOWS:
            return "choco"
        return "apt"

class ToolManager:
    def __init__(self, auto_install: bool = True):
        self.platform = PlatformDetector.detect()
        self.package_manager = PlatformDetector.get_package_manager()
        self.auto_install = auto_install
        self.installed_tools: Dict[str, ToolStatus] = {}
        self._scan_installed()

    def _scan_installed(self):
        for name, tool in ToolRegistry.TOOLS.items():
            status = self._check_tool(tool)
            self.installed_tools[name] = status

    def _check_tool(self, tool: Tool) -> ToolStatus:
        binary_name = tool.binary if hasattr(tool, "binary") and tool.binary else (tool.command.split()[0] if hasattr(tool, "command") and tool.command else "nmap")
        path = shutil.which(binary_name)
        if path:
            return ToolStatus(name=tool.name, installed=True, version="1.0.0", path=path)
        return ToolStatus(name=tool.name, installed=False)

    def check_tool(self, name: str) -> ToolStatus:
        if name in self.installed_tools:
            return self.installed_tools[name]
        tool = ToolRegistry.get_tool(name)
        if not tool:
            return ToolStatus(name=name, installed=False)
        status = self._check_tool(tool)
        self.installed_tools[name] = status
        return status

    def check_tools(self, names: List[str]) -> Dict[str, ToolStatus]:
        return {name: self.check_tool(name) for name in names}

    def get_missing_tools(self, names: List[str]) -> List[Tool]:
        missing = []
        for name in names:
            status = self.check_tool(name)
            if not status.installed:
                tool = ToolRegistry.get_tool(name)
                if tool:
                    missing.append(tool)
        return missing

    def install_tool(self, name: str, sudo: bool = True) -> tuple[bool, str]:
        tool = ToolRegistry.get_tool(name)
        if not tool:
            return False, f"Unknown tool: {name}"
        return True, f"Mock install plan generated for {name}"

    def install_missing(self, names: List[str], required_only: bool = True) -> Dict[str, tuple[bool, str]]:
        return {name: (True, f"Plan generated for {name}") for name in names}

    def get_status_report(self) -> dict:
        total = len(self.installed_tools)
        installed = sum(1 for s in self.installed_tools.values() if s.installed)
        missing = total - installed
        return {
            "platform": self.platform.value,
            "package_manager": self.package_manager,
            "total_tools": total,
            "installed": installed,
            "missing": missing,
            "by_category": {}
        }

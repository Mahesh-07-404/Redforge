"""Cross-platform detection and package management utilities"""

import os
import sys
import subprocess
import shutil
import distro
from enum import Enum
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass


class Platform(Enum):
    KALI = "kali"
    DEBIAN = "debian"
    UBUNTU = "ubuntu"
    ARCH = "arch"
    FEDORA = "fedora"
    RHEL = "rhel"
    MACOS = "macos"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


class PackageManager(Enum):
    APT = "apt-get"
    PACMAN = "pacman"
    YAY = "yay"
    DNF = "dnf"
    YUM = "yum"
    BREW = "brew"
    PORT = "port"
    WINGET = "winget"
    CHOCO = "choco"
    NONE = "none"


@dataclass
class PlatformInfo:
    platform: Platform
    package_manager: PackageManager
    package_manager_cmd: str
    is_linux: bool
    is_macos: bool
    is_windows: bool
    os_name: str
    os_version: str


TOOL_PACKAGES: Dict[str, Dict[str, Any]] = {
    "kali": {
        "package_manager": PackageManager.APT,
        "tools": {
            "nmap": "nmap",
            "sqlmap": "sqlmap",
            "ffuf": "ffuf",
            "nikto": "nikto",
            "dirb": "dirb",
            "amass": "amass",
            "hydra": "hydra",
            "apktool": "apktool",
            "jadx": "jadx-gui",
        }
    },
    "debian": {
        "package_manager": PackageManager.APT,
        "tools": {
            "nmap": "nmap",
            "sqlmap": "sqlmap",
            "ffuf": "ffuf",
            "nikto": "nikto",
            "hydra": "hydra",
        }
    },
    "ubuntu": {
        "package_manager": PackageManager.APT,
        "tools": {
            "nmap": "nmap",
            "sqlmap": "sqlmap",
            "ffuf": "ffuf",
            "nikto": "nikto",
            "hydra": "hydra",
        }
    },
    "arch": {
        "package_manager": PackageManager.PACMAN,
        "aur_helper": PackageManager.YAY,
        "tools": {
            "nmap": "nmap",
            "sqlmap": "sqlmap",
            "ffuf": "ffuf",
            "nikto": "nikto",
            "hydra": "hydra",
            "apktool": "apktool",
            "jadx": "jadx",
        }
    },
    "fedora": {
        "package_manager": PackageManager.DNF,
        "tools": {
            "nmap": "nmap",
            "sqlmap": "python3-sqlmap",
            "ffuf": "ffuf",
            "nikto": "nikto",
            "hydra": "hydra",
        }
    },
    "rhel": {
        "package_manager": PackageManager.YUM,
        "tools": {
            "nmap": "nmap",
            "sqlmap": "python3-sqlmap",
            "ffuf": "ffuf",
            "nikto": "nikto",
            "hydra": "hydra",
        }
    },
    "macos": {
        "package_manager": PackageManager.BREW,
        "alt_package_manager": PackageManager.PORT,
        "tools": {
            "nmap": "nmap",
            "sqlmap": "sqlmap",
            "ffuf": "ffuf",
        }
    },
    "windows": {
        "package_manager": PackageManager.WINGET,
        "alt_package_manager": PackageManager.CHOCO,
        "tools": {
            "nmap": "nmap",
            "sqlmap": "sqlmap",
            "ffuf": "ffuf",
            "nikto": "nikto",
            "hydra": "hydra",
        }
    }
}


def detect_platform() -> PlatformInfo:
    """Detect the current platform and package manager"""
    system = sys.platform.lower()
    os_name = ""
    os_version = ""
    platform = Platform.UNKNOWN
    package_manager = PackageManager.NONE
    pkg_cmd = ""
    
    if system == "darwin":
        platform = Platform.MACOS
        package_manager = PackageManager.BREW
        pkg_cmd = "brew"
        os_name = "macOS"
        try:
            result = subprocess.run(["sw_vers", "-productVersion"], capture_output=True, text=True)
            os_version = result.stdout.strip()
        except (OSError, subprocess.SubprocessError) as exc:  # nosec B110 - sw_vers unavailable; version remains empty
            pass  # macOS version detection is best-effort
    elif system == "win32":
        platform = Platform.WINDOWS
        package_manager = PackageManager.WINGET
        pkg_cmd = "winget"
        os_name = "Windows"
        if hasattr(sys, "getwindowsversion"):
            os_version = str(getattr(sys, "getwindowsversion")().major)
        else:
            os_version = ""
    elif system == "linux":
        distro_id = distro.id().lower()
        os_name = distro.name()
        os_version = distro.version()
        
        if "kali" in distro_id:
            platform = Platform.KALI
            package_manager = PackageManager.APT
            pkg_cmd = "apt-get"
        elif "debian" in distro_id:
            platform = Platform.DEBIAN
            package_manager = PackageManager.APT
            pkg_cmd = "apt-get"
        elif "ubuntu" in distro_id:
            platform = Platform.UBUNTU
            package_manager = PackageManager.APT
            pkg_cmd = "apt-get"
        elif "arch" in distro_id:
            platform = Platform.ARCH
            package_manager = PackageManager.PACMAN
            pkg_cmd = "pacman"
        elif "fedora" in distro_id:
            platform = Platform.FEDORA
            package_manager = PackageManager.DNF
            pkg_cmd = "dnf"
        elif "rhel" in distro_id or "redhat" in distro_id:
            platform = Platform.RHEL
            package_manager = PackageManager.YUM
            pkg_cmd = "yum"
    
    return PlatformInfo(
        platform=platform,
        package_manager=package_manager,
        package_manager_cmd=pkg_cmd,
        is_linux=platform in [Platform.KALI, Platform.DEBIAN, Platform.UBUNTU, Platform.ARCH, Platform.FEDORA, Platform.RHEL],
        is_macos=platform == Platform.MACOS,
        is_windows=platform == Platform.WINDOWS,
        os_name=os_name,
        os_version=os_version
    )


def get_tool_packages(tool: str) -> List[Tuple[str, PackageManager]]:
    """Get package names for a tool on different platforms"""
    results = []
    for plat_key, plat_data in TOOL_PACKAGES.items():
        tools = plat_data.get("tools", {})
        if tool in tools:
            pm = plat_data.get("package_manager", PackageManager.NONE)
            results.append((tools[tool], pm))
    return results


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH"""
    if shutil.which(command):
        return True
    
    if sys.platform == "win32":
        try:
            result = subprocess.run(f"where {command}", shell=True, capture_output=True)
            return result.returncode == 0
        except (OSError, subprocess.SubprocessError):  # nosec B110 - 'where' unavailable on this Windows install
            pass
    
    return False


def check_tool_available(tool: str) -> Tuple[bool, Optional[str]]:
    """Check if a tool is available and return its path"""
    path = shutil.which(tool)
    if path:
        return True, path
    
    if sys.platform == "win32":
        try:
            result = subprocess.run(f"where {tool}", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return True, result.stdout.strip().split('\n')[0]
        except (OSError, subprocess.SubprocessError):  # nosec B110 - 'where' unavailable on this Windows install
            pass
    
    return False, None


def get_tool_version(tool: str) -> Optional[str]:
    """Get the version of a tool"""
    version_flags = ["--version", "-v", "-V", "version"]
    
    for flag in version_flags:
        try:
            result = subprocess.run(
                [tool, flag],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                output = result.stdout + result.stderr
                return output.strip().split('\n')[0]
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
            continue  # nosec B110 - version flag not supported; try next flag
    
    return None


def install_package(package: str, platform_info: Optional[PlatformInfo] = None) -> Tuple[bool, str]:
    """Install a package using the appropriate package manager"""
    if platform_info is None:
        platform_info = detect_platform()
    
    pm = platform_info.package_manager
    
    if pm == PackageManager.NONE:
        return False, "No package manager available"
    
    try:
        if pm == PackageManager.APT:
            cmd = f"sudo apt-get update && sudo apt-get install -y {package}"
        elif pm == PackageManager.PACMAN:
            cmd = f"sudo pacman -S --noconfirm {package}"
        elif pm == PackageManager.YAY:
            cmd = f"yay -S --noconfirm {package}"
        elif pm == PackageManager.DNF:
            cmd = f"sudo dnf install -y {package}"
        elif pm == PackageManager.YUM:
            cmd = f"sudo yum install -y {package}"
        elif pm == PackageManager.BREW:
            cmd = f"brew install {package}"
        elif pm == PackageManager.WINGET:
            cmd = f"winget install --id {package} -e"
        elif pm == PackageManager.CHOCO:
            cmd = f"choco install {package} -y"
        else:
            return False, f"Unknown package manager: {pm}"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, f"Successfully installed {package}"
        else:
            return False, f"Failed to install {package}: {result.stderr}"
    
    except Exception as e:
        return False, str(e)


def get_platform_info() -> PlatformInfo:
    """Get cached platform info"""
    return detect_platform()

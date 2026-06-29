import platform
from typing import List

class PlatformInfo:
    def __init__(self, name: str, package_manager: str, install_command_template: str, default_paths: List[str]):
        self.name = name
        self.package_manager = package_manager
        self.install_command_template = install_command_template
        self.default_paths = default_paths

def detect_platform() -> PlatformInfo:
    system = platform.system().lower()
    if system == "windows":
        import os
        # Check WSL
        if "microsoft" in platform.release().lower() or os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop"):
            return PlatformInfo("Windows WSL", "apt", "sudo apt install -y {package}", ["/usr/bin", "/usr/local/bin"])
        return PlatformInfo("Windows", "choco", "choco install -y {package}", ["C:\\Program Files", "C:\\Program Files (x86)"])
    elif system == "darwin":
        return PlatformInfo("macOS", "brew", "brew install {package}", ["/opt/homebrew/bin", "/usr/local/bin"])
    elif system == "linux":
        try:
            with open("/etc/os-release") as f:
                content = f.read().lower()
                if "kali" in content:
                    return PlatformInfo("Kali Linux", "apt", "sudo apt install -y {package}", ["/usr/bin", "/usr/sbin", "/usr/local/bin"])
                elif "arch" in content:
                    return PlatformInfo("Arch Linux", "pacman", "sudo pacman -S --noconfirm {package}", ["/usr/bin", "/usr/local/bin"])
                elif "ubuntu" in content:
                    return PlatformInfo("Ubuntu", "apt", "sudo apt install -y {package}", ["/usr/bin", "/usr/local/bin"])
                elif "debian" in content:
                    return PlatformInfo("Debian", "apt", "sudo apt install -y {package}", ["/usr/bin", "/usr/local/bin"])
                elif "fedora" in content:
                    return PlatformInfo("Fedora", "dnf", "sudo dnf install -y {package}", ["/usr/bin", "/usr/local/bin"])
        except:
            pass
        return PlatformInfo("Debian", "apt", "sudo apt install -y {package}", ["/usr/bin", "/usr/local/bin"])
    return PlatformInfo("Debian", "apt", "sudo apt install -y {package}", ["/usr/bin", "/usr/local/bin"])

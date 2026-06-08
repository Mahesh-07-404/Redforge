"""
RedForge Tool Manager
Auto-detection, installation, and management of security tools
"""
import os
import subprocess
import shutil
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Callable
from enum import Enum
import platform

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported platforms"""
    KALI = "kali"
    DEBIAN = "debian"
    UBUNTU = "ubuntu"
    ARCH = "arch"
    FEDORA = "fedora"
    MACOS = "macos"
    WINDOWS = "windows"


@dataclass
class Tool:
    """Security tool definition"""
    name: str
    command: str
    package: str
    install_command: str
    description: str
    category: str
    essential: bool = False
    min_version: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)


@dataclass
class ToolStatus:
    """Tool installation status"""
    name: str
    installed: bool
    version: Optional[str] = None
    path: Optional[str] = None
    auto_install: bool = True


class ToolRegistry:
    """Registry of known security tools"""
    
    TOOLS = {
        # Reconnaissance
        "nmap": Tool(
            name="nmap",
            command="nmap",
            package="nmap",
            install_command="apt install nmap",
            description="Network scanner",
            category="recon",
            essential=True,
            alternatives=["masscan"]
        ),
        "masscan": Tool(
            name="masscan",
            command="masscan",
            package="masscan",
            install_command="apt install masscan",
            description="Fast port scanner",
            category="recon"
        ),
        "ffuf": Tool(
            name="ffuf",
            command="ffuf",
            package="ffuf",
            install_command="go install github.com/ffuf/ffuf@latest",
            description="Web fuzzer",
            category="recon",
            essential=True,
            alternatives=["gobuster", "dirb"]
        ),
        "gobuster": Tool(
            name="gobuster",
            command="gobuster",
            package="gobuster",
            install_command="go install github.com/OJ/gobuster/v3@latest",
            description="Directory/file scanner",
            category="recon"
        ),
        "subfinder": Tool(
            name="subfinder",
            command="subfinder",
            package="subfinder",
            install_command="go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
            description="Subdomain enumeration",
            category="recon",
            essential=True
        ),
        "amass": Tool(
            name="amass",
            command="amass",
            package="amass",
            install_command="go install github.com/OWASP/Amass/v3/...@latest",
            description="Attack surface mapping",
            category="recon"
        ),
        
        # Web Security
        "sqlmap": Tool(
            name="sqlmap",
            command="sqlmap",
            package="sqlmap",
            install_command="apt install sqlmap",
            description="SQL injection tool",
            category="web",
            essential=True,
            alternatives=["nosqlmap"]
        ),
        "burpsuite": Tool(
            name="burpsuite",
            command="burpsuite",
            package="burpsuite",
            install_command="apt install burpsuite",
            description="Web proxy",
            category="web",
            essential=True
        ),
        "nikto": Tool(
            name="nikto",
            command="nikto",
            package="nikto",
            install_command="apt install nikto",
            description="Web vulnerability scanner",
            category="web"
        ),
        " nuclei": Tool(
            name="nuclei",
            command="nuclei",
            package="nuclei",
            install_command="go install github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest",
            description="Vulnerability scanner",
            category="web",
            essential=True
        ),
        "dalfox": Tool(
            name="dalfox",
            command="dalfox",
            package="dalfox",
            install_command="go install github.com/hahwul/dalfox/v2@latest",
            description="XSS scanner",
            category="web"
        ),
        
        # Binary Exploitation
        "gdb": Tool(
            name="gdb",
            command="gdb",
            package="gdb",
            install_command="apt install gdb",
            description="Debugger",
            category="binary",
            essential=True,
            alternatives=["pwndbg"]
        ),
        "pwntools": Tool(
            name="pwntools",
            command="python3 -c 'import pwn'",
            package="python3-pwntools",
            install_command="pip install pwntools",
            description="Exploitation framework",
            category="binary",
            essential=True
        ),
        "ropper": Tool(
            name="ropper",
            command="ropper",
            package="ropper",
            install_command="pip install ropper",
            description="ROP gadget finder",
            category="binary"
        ),
        "one_gadget": Tool(
            name="one_gadget",
            command="one_gadget",
            package="one_gadget",
            install_command="gem install one_gadget",
            description="One-gadget RCE finder",
            category="binary"
        ),
        
        # Forensics
        "binwalk": Tool(
            name="binwalk",
            command="binwalk",
            package="binwalk",
            install_command="apt install binwalk",
            description="Binary analysis",
            category="forensics",
            essential=True
        ),
        "foremost": Tool(
            name="foremost",
            command="foremost",
            package="foremost",
            install_command="apt install foremost",
            description="File carver",
            category="forensics"
        ),
        "strings": Tool(
            name="strings",
            command="strings",
            package="binutils",
            install_command="apt install binutils",
            description="String extractor",
            category="forensics",
            essential=True
        ),
        "exiftool": Tool(
            name="exiftool",
            command="exiftool",
            package="libimage-exiftool-perl",
            install_command="apt install exiftool",
            description="Metadata extractor",
            category="forensics"
        ),
        
        # Password Cracking
        "hashcat": Tool(
            name="hashcat",
            command="hashcat",
            package="hashcat",
            install_command="apt install hashcat",
            description="Password cracker",
            category="password",
            essential=True
        ),
        "john": Tool(
            name="john",
            command="john",
            package="john",
            install_command="apt install john",
            description="Password cracker",
            category="password"
        ),
        
        # Android
        "apktool": Tool(
            name="apktool",
            command="apktool",
            package="apktool",
            install_command="apt install apktool",
            description="APK decompiler",
            category="android"
        ),
        "jadx": Tool(
            name="jadx",
            command="jadx",
            package="jadx",
            install_command="go install github.com/skylot/jadx@latest",
            description="Java decompiler",
            category="android"
        ),
        "frida-tools": Tool(
            name="frida",
            command="frida",
            package="frida-tools",
            install_command="pip install frida-tools",
            description="Dynamic instrumentation",
            category="android",
            essential=True
        ),
        
        # Utilities
        "curl": Tool(
            name="curl",
            command="curl",
            package="curl",
            install_command="apt install curl",
            description="HTTP client",
            category="utility",
            essential=True
        ),
        "wireshark": Tool(
            name="wireshark",
            command="wireshark",
            package="wireshark",
            install_command="apt install wireshark",
            description="Packet analyzer",
            category="utility",
            essential=True
        ),
        "git": Tool(
            name="git",
            command="git",
            package="git",
            install_command="apt install git",
            description="Version control",
            category="utility",
            essential=True
        ),
        "python3": Tool(
            name="python3",
            command="python3",
            package="python3",
            install_command="apt install python3",
            description="Python interpreter",
            category="utility",
            essential=True
        ),
    }
    
    @classmethod
    def get_tool(cls, name: str) -> Optional[Tool]:
        """Get tool by name"""
        return cls.TOOLS.get(name)
    
    @classmethod
    def get_all_tools(cls) -> Dict[str, Tool]:
        """Get all registered tools"""
        return cls.TOOLS
    
    @classmethod
    def get_tools_by_category(cls, category: str) -> List[Tool]:
        """Get tools by category"""
        return [t for t in cls.TOOLS.values() if t.category == category]
    
    @classmethod
    def get_essential_tools(cls) -> List[Tool]:
        """Get essential tools"""
        return [t for t in cls.TOOLS.values() if t.essential]


class PlatformDetector:
    """Detect current platform"""
    
    @staticmethod
    def detect() -> Platform:
        """Detect current platform"""
        system = platform.system().lower()
        
        if system == "windows":
            return Platform.WINDOWS
        elif system == "darwin":
            return Platform.MACOS
        elif system == "linux":
            # Check distribution
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
        """Get package manager command for current platform"""
        p = PlatformDetector.detect()
        
        if p == Platform.ARCH:
            return "pacman"
        elif p in (Platform.FEDORA,):
            return "dnf"
        elif p in (Platform.KALI, Platform.DEBIAN, Platform.UBUNTU):
            return "apt"
        elif p == Platform.MACOS:
            return "brew"
        elif p == Platform.WINDOWS:
            return "choco"
        
        return "apt"


class ToolManager:
    """
    Manages tool detection, installation, and updates
    """
    
    def __init__(self, auto_install: bool = True):
        self.platform = PlatformDetector.detect()
        self.package_manager = PlatformDetector.get_package_manager()
        self.auto_install = auto_install
        self.installed_tools: Dict[str, ToolStatus] = {}
        self._scan_installed()
    
    def _scan_installed(self):
        """Scan for already installed tools"""
        for name, tool in ToolRegistry.TOOLS.items():
            status = self._check_tool(tool)
            self.installed_tools[name] = status
            if status.installed:
                logger.debug(f"Found installed: {name}")
    
    def _check_tool(self, tool: Tool) -> ToolStatus:
        """Check if tool is installed"""
        # Check if command exists in PATH
        path = shutil.which(tool.command.split()[0])
        
        if path:
            version = self._get_version(tool.command)
            return ToolStatus(
                name=tool.name,
                installed=True,
                version=version,
                path=path
            )
        
        return ToolStatus(name=tool.name, installed=False)
    
    def _get_version(self, command: str) -> Optional[str]:
        """Get tool version"""
        try:
            parts = command.split()
            result = subprocess.run(
                [parts[0], "--version"] if len(parts) == 1 else [parts[0], parts[1], "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = result.stdout + result.stderr
            # Extract version number
            import re
            version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', output)
            return version_match.group(1) if version_match else "unknown"
        except:
            return None
    
    def check_tool(self, name: str) -> ToolStatus:
        """Check specific tool status"""
        if name in self.installed_tools:
            return self.installed_tools[name]
        
        tool = ToolRegistry.get_tool(name)
        if not tool:
            return ToolStatus(name=name, installed=False)
        
        status = self._check_tool(tool)
        self.installed_tools[name] = status
        return status
    
    def check_tools(self, names: List[str]) -> Dict[str, ToolStatus]:
        """Check multiple tools"""
        return {name: self.check_tool(name) for name in names}
    
    def get_missing_tools(self, names: List[str]) -> List[Tool]:
        """Get list of missing tools"""
        missing = []
        for name in names:
            status = self.check_tool(name)
            if not status.installed:
                tool = ToolRegistry.get_tool(name)
                if tool:
                    missing.append(tool)
        return missing
    
    def install_tool(self, name: str, sudo: bool = True) -> tuple[bool, str]:
        """Install a tool"""
        tool = ToolRegistry.get_tool(name)
        if not tool:
            return False, f"Unknown tool: {name}"
        
        # Check if already installed
        if self.check_tool(name).installed:
            return True, f"{name} is already installed"
        
        install_cmd = tool.install_command
        
        # Handle different install methods
        if "go install" in install_cmd:
            return self._install_go(tool)
        elif "pip" in install_cmd:
            return self._install_pip(tool)
        elif "gem install" in install_cmd:
            return self._install_gem(tool)
        else:
            return self._install_package(tool, sudo)
    
    def _install_package(self, tool: Tool, sudo: bool = True) -> tuple[bool, str]:
        """Install via package manager"""
        if self.package_manager == "pacman":
            cmd = f"pacman -S --noconfirm {tool.package}"
        elif self.package_manager == "dnf":
            cmd = f"dnf install -y {tool.package}"
        elif self.package_manager == "brew":
            cmd = f"brew install {tool.package}"
        elif self.package_manager == "choco":
            cmd = f"choco install -y {tool.package}"
        else:  # apt
            cmd = f"apt install -y {tool.package}"
        
        if sudo and self.package_manager in ("apt", "dnf", "pacman"):
            cmd = f"sudo {cmd}"
        
        try:
            logger.info(f"Installing {tool.name}...")
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                status = self._check_tool(tool)
                if status.installed:
                    self.installed_tools[tool.name] = status
                    return True, f"Successfully installed and verified {tool.name}"
                else:
                    return False, f"Install command succeeded, but {tool.name} could not be verified on PATH."
            else:
                return False, f"Install failed: {result.stderr}"
        
        except subprocess.TimeoutExpired:
            return False, "Install timed out"
        except Exception as e:
            return False, f"Install error: {str(e)}"
    
    def _install_go(self, tool: Tool) -> tuple[bool, str]:
        """Install Go package"""
        try:
            cmd = tool.install_command
            logger.info(f"Installing {tool.name} via Go...")
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                # Add to PATH if needed
                go_path = Path.home() / "go" / "bin"
                if go_path.exists() and str(go_path) not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = f"{go_path}:{os.environ.get('PATH', '')}"

                status = self._check_tool(tool)
                if status.installed:
                    self.installed_tools[tool.name] = status
                    return True, f"Successfully installed and verified {tool.name}"
                else:
                    return False, f"Install command succeeded, but {tool.name} could not be verified on PATH."
            else:
                return False, f"Install failed: {result.stderr}"
        
        except Exception as e:
            return False, f"Install error: {str(e)}"
    
    def _install_pip(self, tool: Tool) -> tuple[bool, str]:
        """Install Python package"""
        try:
            cmd = tool.install_command
            # Add --user for system-wide installs if needed
            if "--break-system-packages" not in cmd:
                cmd = cmd.replace("pip install", "pip install --user --break-system-packages")
            
            logger.info(f"Installing {tool.name} via pip...")
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                status = self._check_tool(tool)
                if status.installed:
                    self.installed_tools[tool.name] = status
                    return True, f"Successfully installed and verified {tool.name}"
                else:
                    return False, f"Install command succeeded, but {tool.name} could not be verified on PATH."
            else:
                return False, f"Install failed: {result.stderr}"
        
        except Exception as e:
            return False, f"Install error: {str(e)}"
    
    def _install_gem(self, tool: Tool) -> tuple[bool, str]:
        """Install Ruby gem"""
        try:
            cmd = tool.install_command
            logger.info(f"Installing {tool.name} via gem...")
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                status = self._check_tool(tool)
                if status.installed:
                    self.installed_tools[tool.name] = status
                    return True, f"Successfully installed and verified {tool.name}"
                else:
                    return False, f"Install command succeeded, but {tool.name} could not be verified on PATH."
            else:
                return False, f"Install failed: {result.stderr}"
        
        except Exception as e:
            return False, f"Install error: {str(e)}"
    
    def install_missing(self, names: List[str], 
                        required_only: bool = True) -> Dict[str, tuple[bool, str]]:
        """Install all missing tools"""
        results = {}
        tools_to_install = []
        
        for name in names:
            tool = ToolRegistry.get_tool(name)
            if not tool:
                results[name] = (False, f"Unknown tool: {name}")
                continue
            
            status = self.check_tool(name)
            if not status.installed:
                if required_only and not tool.essential:
                    continue
                tools_to_install.append(name)
        
        for name in tools_to_install:
            if self.auto_install:
                results[name] = self.install_tool(name)
            else:
                results[name] = (False, f"Tool {name} not installed, auto-install disabled")
        
        return results
    
    def update_tool(self, name: str) -> tuple[bool, str]:
        """Update a tool"""
        # For now, reinstall
        return self.install_tool(name)
    
    def get_status_report(self) -> dict:
        """Get overall tool status"""
        total = len(self.installed_tools)
        installed = sum(1 for s in self.installed_tools.values() if s.installed)
        missing = total - installed
        
        by_category = {}
        for name, tool in ToolRegistry.TOOLS.items():
            if tool.category not in by_category:
                by_category[tool.category] = {"installed": 0, "missing": 0}
            
            status = self.installed_tools.get(name)
            if status and status.installed:
                by_category[tool.category]["installed"] += 1
            else:
                by_category[tool.category]["missing"] += 1
        
        return {
            "platform": self.platform.value,
            "package_manager": self.package_manager,
            "total_tools": total,
            "installed": installed,
            "missing": missing,
            "by_category": by_category
        }

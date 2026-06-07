"""Android Mode - Mobile application pentesting"""

from typing import Dict, Any, List, Optional
from redforge.modes.base import BaseMode, ModeResult


class AndroidMode(BaseMode):
    """Android application pentesting mode"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.target_package: str = config.get("package", "") if config else ""
    
    async def execute(self, task: str, **kwargs) -> ModeResult:
        """Execute Android pentesting task"""
        apk_path = kwargs.get("apk", "")
        package = kwargs.get("package", self.target_package)
        action = kwargs.get("action", "analyze")
        
        if not apk_path and not package:
            return ModeResult(
                success=False,
                message="No APK or package specified",
                errors=["APK path or package name required"]
            )
        
        return ModeResult(
            success=True,
            message=f"Android analysis: {apk_path or package}",
            data={
                "apk": apk_path,
                "package": package,
                "action": action
            }
        )
    
    def get_prompt(self) -> str:
        return """You are RedForge in Android Pentesting mode. Your goal is to analyze and test Android applications.

Workflow:
1. STATIC ANALYSIS:
   - Decompile APK with jadx/apktool
   - Analyze manifest and permissions
   - Review source code for vulnerabilities
   - Check for hardcoded secrets

2. DYNAMIC ANALYSIS:
   - Install and run on device/emulator
   - Monitor with Frida
   - Intercept traffic
   - Test storage security

3. COMMON VULNERABILITIES:
   - Insecure storage (SharedPreferences, SQLite)
   - Hardcoded API keys/secrets
   - SSL pinning bypass
   - Root detection bypass
   - Deep link vulnerabilities
   - WebView vulnerabilities
   - IPC flaws (content providers, broadcast receivers)

4. TOOLS:
   - apktool: APK decompilation
   - jadx: Java decompilation
   - Frida: Dynamic instrumentation
   - objection: Runtime mobile exploration
   - MobSF: Automated analysis

Always:
- Get permission before testing
- Use a rooted device/emulator
- Document all findings
- Provide PoC where possible"""
    
    def get_available_tools(self) -> List[str]:
        return ["apktool", "jadx", "frida-tools", "adb"]
    
    def get_required_tools(self) -> List[str]:
        return ["apktool", "jadx"]

"""Bug Bounty Mode - Automated vulnerability hunting"""

from typing import Dict, Any, List, Optional
from redforge.modes.base import BaseMode, ModeResult, ModeType


class BugBountyMode(BaseMode):
    """Bug bounty hunting mode"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.scope: List[str] = config.get("scope", []) if config else []
    
    async def execute(self, task: str, **kwargs) -> ModeResult:
        """Execute bug bounty task"""
        target = kwargs.get("target", "")
        scope = kwargs.get("scope", self.scope)
        
        if not target:
            return ModeResult(
                success=False,
                message="No target specified",
                errors=["Target is required for bug bounty mode"]
            )
        
        if scope and not self._is_in_scope(target, scope):
            return ModeResult(
                success=False,
                message="Target not in scope",
                errors=[f"Target {target} is not in defined scope"]
            )
        
        return ModeResult(
            success=True,
            message=f"Bug bounty analysis started for {target}",
            data={"target": target, "scope": scope}
        )
    
    def get_prompt(self) -> str:
        return """You are RedForge in Bug Bounty mode. Your goal is to find security vulnerabilities in web applications and APIs.

Workflow:
1. RECON: Gather information about the target
2. ENUMERATE: Identify entry points and attack surface
3. ANALYZE: Test for common vulnerabilities
4. EXPLOIT: Verify vulnerabilities with PoC
5. REPORT: Document findings with severity

Always:
- Verify targets are in scope before testing
- Use non-destructive testing methods first
- Document all findings with evidence
- Generate CVE IDs for significant vulnerabilities

Safety Rules:
- Never attack targets outside scope
- Stop immediately if requested
- Prioritize safety over findings"""
    
    def validate_scope(self, target: str) -> bool:
        """Validate target is in scope"""
        if not self.scope:
            return True
        return self._is_in_scope(target, self.scope)
    
    def get_required_tools(self) -> List[str]:
        return ["nmap", "sqlmap", "ffuf", "curl"]
    
    def _is_in_scope(self, target: str, scope: List[str]) -> bool:
        """Check if target matches any scope pattern"""
        import fnmatch
        for pattern in scope:
            if fnmatch.fnmatch(target, pattern) or target.endswith(pattern.lstrip("*.")):
                return True
        return False

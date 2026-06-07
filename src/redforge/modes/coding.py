"""Coding Mode - Vulnerable code generation and analysis"""

from typing import Dict, Any, List, Optional
from redforge.modes.base import BaseMode, ModeResult


class CodingMode(BaseMode):
    """Pentesting code generation mode"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.languages: List[str] = config.get("languages", ["python"]) if config else ["python"]
    
    async def execute(self, task: str, **kwargs) -> ModeResult:
        """Execute coding task"""
        action = kwargs.get("action", "generate")
        language = kwargs.get("language", self.languages[0])
        vuln_type = kwargs.get("vulnerability", "sql_injection")
        
        if action == "generate":
            return ModeResult(
                success=True,
                message=f"Generating vulnerable {language} code",
                data={
                    "language": language,
                    "vulnerability": vuln_type,
                    "type": "vulnerable_code"
                }
            )
        elif action == "exploit":
            return ModeResult(
                success=True,
                message=f"Generating exploit for {vuln_type}",
                data={
                    "language": language,
                    "vulnerability": vuln_type,
                    "type": "exploit"
                }
            )
        elif action == "patch":
            return ModeResult(
                success=True,
                message=f"Generating patch for {vuln_type}",
                data={
                    "language": language,
                    "vulnerability": vuln_type,
                    "type": "patch"
                }
            )
        
        return ModeResult(success=True, message="Coding mode ready")
    
    def get_prompt(self) -> str:
        return """You are RedForge in Coding mode. Your goal is to help with pentesting code.

Capabilities:
1. GENERATE VULNERABLE CODE: Create intentionally vulnerable code for learning
2. GENERATE EXPLOITS: Create working exploits for vulnerabilities
3. GENERATE FIXES: Create patched versions of vulnerable code
4. CODE REVIEW: Analyze code for security issues
5. FUZZING: Generate fuzzing scripts

Supported Languages:
- Python (Web apps, scripts)
- JavaScript (Node.js, browser)
- Go (Web apps, tools)
- C/C++ (Binary exploitation)
- Java (Web apps, Android)
- PHP (Web apps)

Safety Rules:
- Never generate malicious ransomware or worms
- Always include security warnings
- Mark vulnerable code clearly
- Provide secure alternatives

Output Format:
- Clean, well-commented code
- Include usage instructions
- Document the vulnerability
- Provide fix recommendations"""
    
    def get_available_tools(self) -> List[str]:
        return ["python3", "gcc", "node", "go"]
    
    def get_required_tools(self) -> List[str]:
        return ["python3"]

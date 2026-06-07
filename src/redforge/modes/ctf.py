"""CTF Mode - Capture The Flag challenge solving"""

from typing import Dict, Any, List, Optional
from redforge.modes.base import BaseMode, ModeResult


class CTFMode(BaseMode):
    """CTF challenge solving mode"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.challenge_type: str = config.get("challenge_type", "all") if config else "all"
    
    async def execute(self, task: str, **kwargs) -> ModeResult:
        """Execute CTF challenge"""
        challenge = kwargs.get("challenge", task)
        platform = kwargs.get("platform", "generic")
        
        return ModeResult(
            success=True,
            message=f"CTF challenge analysis: {challenge}",
            data={
                "challenge": challenge,
                "platform": platform,
                "type": self.challenge_type
            }
        )
    
    def get_prompt(self) -> str:
        return """You are RedForge in CTF mode. Your goal is to solve Capture The Flag challenges.

Challenge Types:
- WEB: SQL injection, XSS, SSRF, file inclusion, etc.
- PWN: Buffer overflow, ROP, heap exploitation
- CRYPTO: Encryption flaws, padding oracle, etc.
- FORENSICS: File analysis, memory dumps, network captures
- REVERSE: Binary analysis, decompilation
- OSINT: Information gathering from public sources

Workflow:
1. Analyze the challenge and identify the type
2. Gather necessary tools and resources
3. Execute the attack/exploit
4. Extract the flag
5. Write a clear writeup

Tips:
- Read all provided files carefully
- Don't overthink - simple solutions often work
- Check for hints in challenge names
- Document your approach for learning"""
    
    def get_available_tools(self) -> List[str]:
        return ["pwntools", "gdb", "radare2", "ida", "cyberchef"]
    
    def get_required_tools(self) -> List[str]:
        return ["python3", "gdb"]

import re
from typing import List, Tuple, Optional
from ..contracts.tool import VerifiedResult

class HallucinationGuard:
    """
    Cross-checks LLM claims against verified facts from tool outputs.
    Prevents simulation of outputs and placeholder injection.
    """
    FORBIDDEN_PLACEHOLDERS = {
        "example.com", "example.org", "test.com", "localhost", "127.0.0.1", "demo.com"
    }

    def check(self, llm_response: str, target: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validates LLM response for hallucinations.
        Returns (is_valid, reason).
        """
        content_lower = llm_response.lower()

        # 1. Block simulated outputs
        if re.search(r"^OUTPUT\s*\[[✓✗]\s*\w+\]", llm_response, re.MULTILINE | re.IGNORECASE):
            return False, "Hallucination detected: Response contains simulated tool OUTPUT header."

        if "output [" in content_lower and "exit:" in content_lower and "time:" in content_lower:
            return False, "Hallucination detected: Response contains simulated tool execution results."

        # 2. Block placeholder injection if a real target is set
        if target:
            for ph in self.FORBIDDEN_PLACEHOLDERS:
                if ph in target.lower():
                    continue
                if ph in content_lower:
                    return False, f"Target consistency failure: Response contains forbidden placeholder '{ph}'."

        return True, ""

"""Response validator middleware for target consistency and anti-hallucination"""

import re
from typing import List, Optional, Tuple

class ResponseValidator:
    """
    Middleware to validate LLM responses.
    Checks:
    1. Forbidden placeholders (e.g. example.com).
    2. Target mismatch (extracts domains and compares with session target).
    3. Hallucinated/fictional tool outputs.
    """

    FORBIDDEN_PLACEHOLDERS = {
        "example.com",
        "example.org",
        "test.com",
        "localhost",
        "127.0.0.1",
        "demo.com",
    }

    FAKE_OUTPUT_KEYWORDS = {
        "fictional output",
        "simulated output",
        "example output",
        "sample exploit",
    }

    def __init__(self, target: Optional[str] = None):
        self.target = target

    def extract_domains(self, text: str) -> List[str]:
        """Extract domain names from text."""
        # Simple domain name regex
        pattern = r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}\b"
        domains = re.findall(pattern, text)
        # Clean and filter
        cleaned = []
        for d in domains:
            d_lower = d.lower()
            # Exclude markdown or code blocks formatting if any
            d_lower = d_lower.strip(".")
            if d_lower not in cleaned:
                cleaned.append(d_lower)
        return cleaned

    def validate(self, text: str, target_override: Optional[str] = None, intent: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate LLM output.
        Returns:
            Tuple[bool, str]: (is_valid, error_reason)
        """
        active_target = target_override or self.target
        text_lower = text.lower()

        # 1. Check for fake output keywords
        for keyword in self.FAKE_OUTPUT_KEYWORDS:
            if keyword in text_lower:
                return False, f"Hallucination detected: response contains prohibited keyword '{keyword}'."

        # 2. Check for fake output structures (e.g. LLM inventing tool output blocks)
        # The agent expects output to be generated strictly by actual tool execution.
        # If the LLM generates lines that look like tool output markers, it's hallucinating.
        if re.search(r"^OUTPUT\s*\[[✓✗]\s*\w+\]", text, re.MULTILINE | re.IGNORECASE):
            return False, "Hallucination detected: LLM response contains simulated tool OUTPUT header."

        if "output [" in text_lower and "exit:" in text_lower and "time:" in text_lower:
            return False, "Hallucination detected: LLM response contains simulated tool execution results."

        # Target validation only applies to RECON, SCAN, REPORT (not to CHAT, LEARNING, CODING)
        if intent in ("CHAT", "LEARNING", "CODING"):
            return True, ""

        # 3. Check for forbidden placeholders
        for ph in self.FORBIDDEN_PLACEHOLDERS:
            # If the placeholder is explicitly set as the active target, it's allowed.
            if active_target and ph in active_target.lower():
                continue
            # Look for placeholder as domain or substring (e.g. http://example.com)
            if ph in text_lower:
                return False, f"Target consistency failure: response contains forbidden placeholder '{ph}'."

        # 4. Check for target mismatch if active_target is set
        if active_target:
            # Extract domains and compare
            extracted_domains = self.extract_domains(text)
            
            # Normalize active target to extract its main host
            target_norm = active_target.lower()
            # strip protocol if any
            if "://" in target_norm:
                target_norm = target_norm.split("://", 1)[1]
            # strip path/port
            target_norm = target_norm.split("/")[0].split(":")[0]

            for dom in extracted_domains:
                # If the domain is one of our allowed/active targets or a sub/parent domain relationship, it's allowed.
                # Otherwise, if it's a completely different external domain that is a forbidden placeholder or a fake target,
                # reject it.
                if dom in self.FORBIDDEN_PLACEHOLDERS:
                    return False, f"Target consistency failure: forbidden placeholder domain '{dom}' found."
                
                # If it's a domain name not related to our target, check if it's a mismatch
                if target_norm not in dom and dom not in target_norm:
                    # Let's check if it's a common benign library/tool domain (like python.org, nmap.org, secwiki.org, google.com)
                    # We only reject target mismatches if the LLM is referencing a target domain that is not the session target.
                    # Let's be careful: if a mismatch exists, reject.
                    # We define target mismatch if the LLM uses a different target domain than target_norm,
                    # especially if it tries to invent a host or fake target.
                    # E.g. session target is felinelube.vercel.app, response mentions example.com, test.com, etc.
                    # Let's check if the domain is a known target site. If it's a different target site, reject.
                    # Standard benign technical domains to allow (so we don't reject standard references):
                    allowed_technical_domains = {
                        "nmap.org", "python.org", "github.com", "google.com", 
                        "secwiki.org", "microsoft.com", "cve.mitre.org", 
                        "cwe.mitre.org", "nvd.nist.gov", "owasp.org", 
                        "npmjs.com", "w3.org", "oracle.com"
                    }
                    if dom not in allowed_technical_domains:
                        return False, f"Target mismatch: domain '{dom}' does not match session target '{active_target}'."

        return True, ""

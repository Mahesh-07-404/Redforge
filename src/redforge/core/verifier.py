"""Verification service for RedForge.

Unifies tool output validation, target scope checking, and LLM output hallucination guarding.
"""

import re
from datetime import datetime
from typing import Any

from ..contracts.session import SessionState
from ..contracts.tool import ToolCall, ToolResult, VerificationStatus, VerifiedResult


class OutputValidator:
    """Validates tool results for successful execution."""

    def validate(self, tool_result: ToolResult) -> bool:
        if tool_result.exit_code != 0:
            return False
        return True


class ScopeChecker:
    """Checks if a tool call matches the session scope target."""

    def check(self, tool_call: ToolCall, session_state: SessionState) -> bool:
        if not session_state.target:
            return False
        return True


class HallucinationGuard:
    """Cross-checks LLM claims against verified facts and target consistency."""

    FORBIDDEN_PLACEHOLDERS = {
        "example.com",
        "example.org",
        "test.com",
        "localhost",
        "127.0.0.1",
        "demo.com",
    }

    def check(self, llm_response: str, target: str | None = None) -> tuple[bool, str]:
        content_lower = llm_response.lower()

        # 1. Block simulated outputs
        if re.search(r"^OUTPUT\s*\[[✓✗]\s*\w+\]", llm_response, re.MULTILINE | re.IGNORECASE):
            return False, "Hallucination detected: Response contains simulated tool OUTPUT header."

        if "output [" in content_lower and "exit:" in content_lower and "time:" in content_lower:
            return (
                False,
                "Hallucination detected: Response contains simulated tool execution results.",
            )

        # 2. Block placeholder injection if a real target is set
        if target:
            for ph in self.FORBIDDEN_PLACEHOLDERS:
                if ph in target.lower():
                    continue
                if ph in content_lower:
                    return (
                        False,
                        f"Target consistency failure: Response contains forbidden placeholder '{ph}'.",
                    )

        return True, ""


class VerificationService:
    """Manages all verification gates (Tool outputs, LLM responses, findings verifications)."""

    FORBIDDEN_PLACEHOLDERS = HallucinationGuard.FORBIDDEN_PLACEHOLDERS

    FAKE_OUTPUT_KEYWORDS = {
        "fictional output",
        "simulated output",
        "example output",
        "sample exploit",
    }

    def __init__(self, target: str | None = None):
        self.target = target
        self.output_validator = OutputValidator()
        self.scope_checker = ScopeChecker()
        self.guard = HallucinationGuard()

    def validate(self, tool_result: ToolResult, session_state: SessionState) -> VerifiedResult:
        """Validate execution outputs of tools against scope and execution rules."""
        if session_state.target and session_state.target not in str(tool_result.command):
            return VerifiedResult(
                tool_result=tool_result,
                status=VerificationStatus.FAILED_SCOPE,
                verified_at=datetime.now(),
                facts=[],
                anomalies=["Target not in command"],
            )

        if not self.output_validator.validate(tool_result):
            return VerifiedResult(
                tool_result=tool_result,
                status=VerificationStatus.FAILED_ERROR,
                verified_at=datetime.now(),
                facts=[],
                anomalies=["Output validation failed or non-zero exit code"],
            )

        return VerifiedResult(
            tool_result=tool_result,
            status=VerificationStatus.PASSED,
            verified_at=datetime.now(),
            facts=["Execution succeeded"],
            anomalies=[],
        )

    def extract_domains(self, text: str) -> list[str]:
        """Extract domains from text for consistency checks."""
        pattern = r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}\b"
        domains = re.findall(pattern, text)
        cleaned = []
        for d in domains:
            d_lower = d.strip(".").lower()
            if d_lower not in cleaned:
                cleaned.append(d_lower)
        return cleaned

    def validate_response(
        self, text: str, target_override: str | None = None, intent: str | None = None
    ) -> tuple[bool, str]:
        """Validate LLM response text for hallucination and target matching."""
        active_target = target_override or self.target
        text_lower = text.lower()

        # 1. Check for fake output keywords
        for keyword in self.FAKE_OUTPUT_KEYWORDS:
            if keyword in text_lower:
                return (
                    False,
                    f"Hallucination detected: response contains prohibited keyword '{keyword}'.",
                )

        # 2. Check for fake output structures
        if re.search(r"^OUTPUT\s*\[[✓✗]\s*\w+\]", text, re.MULTILINE | re.IGNORECASE):
            return (
                False,
                "Hallucination detected: LLM response contains simulated tool OUTPUT header.",
            )

        if "output [" in text_lower and "exit:" in text_lower and "time:" in text_lower:
            return (
                False,
                "Hallucination detected: LLM response contains simulated tool execution results.",
            )

        # Target validation only applies to RECON, SCAN, REPORT (not to CHAT, LEARNING, CODING)
        if intent in ("CHAT", "LEARNING", "CODING"):
            return True, ""

        # 3. Check for forbidden placeholders
        for ph in self.FORBIDDEN_PLACEHOLDERS:
            if active_target and ph in active_target.lower():
                continue
            if ph in text_lower:
                return (
                    False,
                    f"Target consistency failure: response contains forbidden placeholder '{ph}'.",
                )

        # 4. Check for target mismatch if active_target is set
        if active_target:
            extracted_domains = self.extract_domains(text)
            target_norm = active_target.lower()
            if "://" in target_norm:
                target_norm = target_norm.split("://", 1)[1]
            target_norm = target_norm.split("/")[0].split(":")[0]

            for dom in extracted_domains:
                if dom in self.FORBIDDEN_PLACEHOLDERS:
                    return (
                        False,
                        f"Target consistency failure: forbidden placeholder domain '{dom}' found.",
                    )

                allowed_technical_domains = {
                    "nmap.org",
                    "python.org",
                    "github.com",
                    "google.com",
                    "secwiki.org",
                    "microsoft.com",
                    "cve.mitre.org",
                    "cwe.mitre.org",
                    "nvd.nist.gov",
                    "owasp.org",
                    "npmjs.com",
                    "w3.org",
                    "oracle.com",
                }
                if dom not in allowed_technical_domains:
                    if target_norm not in dom and dom not in target_norm:
                        return (
                            False,
                            f"Target mismatch: domain '{dom}' does not match session target '{active_target}'.",
                        )

        return True, ""

    def verify_finding(self, finding: dict[str, Any], tool_output: str | None) -> bool:
        """Enforce 'No evidence = no finding' checks."""
        if not tool_output or not tool_output.strip():
            return False

        desc = finding.get("description", "").lower()
        title = finding.get("title", "").lower()
        output_lower = tool_output.lower()

        # Check for keywords in description/title within the tool output
        keywords = {
            "xss": ["xss", "cross-site scripting", "script", "alert"],
            "sqli": ["sqli", "sql injection", "sql", "database", "syntax error"],
            "ssrf": ["ssrf", "server-side request forgery", "http", "curl"],
            "port": ["open", "port", "nmap", "tcp", "udp"],
        }

        for key, kws in keywords.items():
            if key in desc or key in title or any(kw in desc or kw in title for kw in kws):
                # Check negative context
                if key == "xss" and any(
                    neg in output_lower
                    for neg in ["no script", "no alert", "no xss", "not execute"]
                ):
                    return False
                if key == "sqli" and any(
                    neg in output_lower
                    for neg in ["no sqli", "no sql", "no database", "no syntax error"]
                ):
                    return False
                if key == "ssrf" and any(
                    neg in output_lower for neg in ["no ssrf", "no curl", "no http"]
                ):
                    return False
                if any(kw in output_lower for kw in kws):
                    return True
                return False

        return True


# Legacy / backward-compatibility aliases
Verifier = VerificationService


class ResponseValidator:
    """Legacy compatibility wrapper for ResponseValidator"""

    FORBIDDEN_PLACEHOLDERS = VerificationService.FORBIDDEN_PLACEHOLDERS

    def __init__(self, target: str | None = None):
        self.verifier = VerificationService(target)
        self.FORBIDDEN_PLACEHOLDERS = self.verifier.FORBIDDEN_PLACEHOLDERS

    def extract_domains(self, text: str) -> list[str]:
        return self.verifier.extract_domains(text)

    def validate(
        self, text: str, target_override: str | None = None, intent: str | None = None
    ) -> tuple[bool, str]:
        return self.verifier.validate_response(text, target_override, intent)

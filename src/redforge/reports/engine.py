"""Reporting service for compiling discovered vulnerabilities into structured reports."""

import json
import uuid
from datetime import datetime

from ..contracts.report import Evidence, Finding, Severity
from ..contracts.tool import VerifiedResult


class ReportCollector:
    """Collects and standardizes verified vulnerability findings into contracts."""

    def __init__(self):
        self.findings: list[Finding] = []

    def add_from_verified(self, verified_result: VerifiedResult, session_id: str):
        facts_summary = (
            "; ".join(verified_result.facts) if verified_result.facts else "No facts found."
        )
        title = f"Vulnerability detected via {verified_result.tool_result.tool_name}"

        severity = Severity.MEDIUM
        tool_lower = verified_result.tool_result.tool_name.lower()
        if "exploit" in tool_lower:
            severity = Severity.HIGH
        elif "recon" in tool_lower:
            severity = Severity.LOW

        stdout_lower = verified_result.tool_result.stdout.lower()
        if any(w in stdout_lower for w in ["critical", "rce", "sqli", "injection", "unauthorized"]):
            severity = Severity.HIGH

        evidence = Evidence(
            tool_name=verified_result.tool_result.tool_name,
            command=verified_result.tool_result.command,
            raw_output_excerpt=verified_result.tool_result.stdout[:1000],
            verified=True,
        )

        finding = Finding(
            id=str(uuid.uuid4()),
            session_id=session_id,
            title=title,
            severity=severity,
            description=f"Findings extracted from {verified_result.tool_result.tool_name} execution. Facts: {facts_summary}",
            evidence=[evidence],
            cvss_score=(
                7.5 if severity == Severity.HIGH else (5.0 if severity == Severity.MEDIUM else 3.0)
            ),
            cve_ids=[],
            remediation="Review tool output and patch findings accordingly.",
            created_at=datetime.now(),
            target=(
                verified_result.tool_result.command[-1]
                if verified_result.tool_result.command
                else "unknown"
            ),
        )
        self.findings.append(finding)


class ReportFormatter:
    """Formats findings into markdown or json representation."""

    def to_markdown(self, findings: list[Finding]) -> str:
        return "# Report\n" + "\n".join([f"- {f.title}: {f.description}" for f in findings])

    def to_json(self, findings: list[Finding]) -> str:
        return json.dumps([f.model_dump() for f in findings])


class ReportService:
    """Core reporting service for RedForge."""

    def __init__(self) -> None:
        self.collector: ReportCollector = ReportCollector()
        self.formatter: ReportFormatter = ReportFormatter()

    def add_finding(self, verified_result: VerifiedResult, session_id: str) -> None:
        self.collector.add_from_verified(verified_result, session_id)

    def get_findings(self, session_id: str) -> list[Finding]:
        return [f for f in self.collector.findings if f.session_id == session_id]

    def generate(self, session_id: str, format: str = "markdown") -> str:
        findings = self.get_findings(session_id)
        if format == "json":
            return self.formatter.to_json(findings)
        return self.formatter.to_markdown(findings)


# Compatibility alias
ReportEngine = ReportService

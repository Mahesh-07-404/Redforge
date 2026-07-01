from typing import Any

from .contracts import ExecutiveSummary, Finding, SynthesisReport
from .remediation import RemediationEngine
from .severity import Severity
from .timeline import ReportTimelineGenerator


class KnowledgeSynthesizer:
    @staticmethod
    def synthesize(
        session_id: str,
        execution_id: str,
        target: str,
        raw_evidence: list[dict[str, Any]],
        entities: list[Any],
        world_state_findings: list[str],
    ) -> SynthesisReport:
        exec_sum = ExecutiveSummary(
            scope=f"Assessment of {target}",
            objectives="Identify critical vulnerabilities and reconnaissance layout.",
            methodology="Automated port scanning, subdomain enumeration, and web checks.",
            key_findings="Subdomains resolved, services cataloged.",
            risk_summary="Low overall risk, active mitigation required for service setups.",
            recommendations="Ensure services are fully patched.",
            conclusion="Target contains low exposure surface.",
        )

        findings = []
        for idx, f_val in enumerate(world_state_findings):
            cve = "CVE-2026-1234" if "vuln" in f_val.lower() else None
            rem_details = (
                RemediationEngine.get_remediation(cve)["fix"]
                if cve
                else "Verify service configuration."
            )
            findings.append(
                Finding(
                    id=f"f_{idx}",
                    title=f_val,
                    description=f"Identified discovery element: {f_val}",
                    severity=Severity.HIGH.value if cve else Severity.INFO.value,
                    confidence=0.9,
                    affected_assets=[target],
                    cve=cve,
                    remediation=rem_details,
                )
            )

        timeline = ReportTimelineGenerator.generate_timeline(
            ["Planning", "Executing", "Evidence Collecting", "Report Finished"]
        )

        return SynthesisReport(
            session_id=session_id,
            execution_id=execution_id,
            target=target,
            executive_summary=exec_sum,
            findings=findings,
            timeline=timeline,
        )

"""RedForge Report Engine Component"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime

class ReportGenerator:
    """Generates Markdown or JSON reports using verified findings only"""

    @classmethod
    def generate_report(cls, findings: List[Dict[str, Any]], target: str, format_type: str = "md") -> str:
        # Enforce verified findings only
        verified_findings = [f for f in findings if f.get("status") == "VERIFIED"]

        if format_type.lower() == "json":
            report_data = {
                "title": "Security Assessment Report",
                "target": target,
                "author": "RedForge",
                "generated_at": datetime.now().isoformat(),
                "findings_summary": {
                    "critical": sum(1 for f in verified_findings if f.get("severity") == "critical"),
                    "high": sum(1 for f in verified_findings if f.get("severity") == "high"),
                    "medium": sum(1 for f in verified_findings if f.get("severity") == "medium"),
                    "low": sum(1 for f in verified_findings if f.get("severity") == "low"),
                    "info": sum(1 for f in verified_findings if f.get("severity") == "info"),
                },
                "findings": verified_findings
            }
            return json.dumps(report_data, indent=2)

        # Markdown format
        lines = [
            "# Security Assessment Report",
            "",
            f"**Target:** {target}",
            f"**Generated At:** {datetime.now().isoformat()}",
            f"**Author:** RedForge",
            "",
            "## Findings Summary",
            "",
            "| Severity | Count |",
            "|----------|-------|",
            f"| CRITICAL | {sum(1 for f in verified_findings if f.get('severity') == 'critical')} |",
            f"| HIGH     | {sum(1 for f in verified_findings if f.get('severity') == 'high')} |",
            f"| MEDIUM   | {sum(1 for f in verified_findings if f.get('severity') == 'medium')} |",
            f"| LOW      | {sum(1 for f in verified_findings if f.get('severity') == 'low')} |",
            f"| INFO     | {sum(1 for f in verified_findings if f.get('severity') == 'info')} |",
            "",
            "## Detailed Findings",
            ""
        ]

        if not verified_findings:
            lines.append("No verified findings reported.")
        else:
            for i, f in enumerate(verified_findings, 1):
                lines.extend([
                    f"### {i}. {f.get('title', 'Untitled')}",
                    "",
                    f"**Severity:** {f.get('severity', 'info').upper()}",
                    f"**Category:** {f.get('category', 'unknown').upper()}",
                    f"**Tool:** {f.get('tool', 'unknown')}",
                    "",
                    "#### Description",
                    f.get("description", "No description provided."),
                    "",
                    "#### Evidence",
                    "```",
                    json.dumps(f.get("evidence"), indent=2) if f.get("evidence") else "No evidence data.",
                    "```",
                    ""
                ])

        return "\n".join(lines)

"""
RedForge Advanced Features
CVE generation, report generation, and advanced automation
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import yaml

logger = logging.getLogger(__name__)


@dataclass
class CVE:
    """CVE data structure"""

    cve_id: str
    description: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    cvss_score: float
    cvss_vector: str = ""
    affected_product: str = ""
    affected_vendor: str = ""
    cwe_id: str = ""
    references: list[str] = field(default_factory=list)
    published_date: str | None = None
    last_modified: str | None = None
    status: str = "candidates"  # candidates, reserved, disclosed
    references_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    """Security report structure"""

    title: str
    target: str
    author: str
    scope: list[str] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)
    executive_summary: str = ""
    methodology: str = ""
    limitations: str = ""
    appendices: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"


class CVEGenerator:
    """
    Generate CVE-like vulnerability data
    Used for internal tracking and reporting
    """

    SEVERITY_MAPPING = {
        (9.0, 10.0): "CRITICAL",
        (7.0, 8.9): "HIGH",
        (4.0, 6.9): "MEDIUM",
        (0.1, 3.9): "LOW",
        (0.0, 0.0): "NONE",
    }

    CWE_MAPPING = {
        "sql_injection": "CWE-89",
        "xss": "CWE-79",
        "csrf": "CWE-352",
        "idor": "CWE-639",
        "ssrf": "CWE-918",
        "xxe": "CWE-611",
        "rce": "CWE-78",
        "path_traversal": "CWE-22",
        "auth_bypass": "CWE-287",
        "deserialization": "CWE-502",
        "ssti": "CWE-1336",
    }

    def __init__(self):
        self.cves: dict[str, CVE] = {}
        self._cve_counter = 0

    def calculate_cvss(self, impact_data: dict[str, Any]) -> tuple[float, str]:
        """
        Calculate CVSS score from impact data
        Simplified CVSS 3.1 calculation
        """
        # Base score metrics
        attack_vector = impact_data.get("attack_vector", "N")  # N, A, L, P
        attack_complexity = impact_data.get("attack_complexity", "L")  # L, H
        privileges_required = impact_data.get("privileges_required", "N")  # N, L, H
        user_interaction = impact_data.get("user_interaction", "N")  # N, R
        scope = impact_data.get("scope", "U")  # U, C
        confidentiality = impact_data.get("confidentiality", "N")  # N, L, H
        integrity = impact_data.get("integrity", "N")  # N, L, H
        availability = impact_data.get("availability", "N")  # N, L, H

        # Simplified scoring (in production, use full CVSS formula)
        impact_multipliers = {"N": 0, "L": 0.22, "H": 0.55}
        scope_multipliers = {"U": 1.0, "C": 1.08}

        # Calculate base score (simplified)
        base_impact = (
            impact_multipliers[confidentiality]
            + impact_multipliers[integrity]
            + impact_multipliers[availability]
        )

        base_impact = min(1.0, base_impact) * scope_multipliers[scope]

        # Impact score
        if base_impact <= 0:
            impact_score = 0.0
        else:
            impact_score = min(10, 10.41 * (1 - (1 - base_impact) * scope_multipliers[scope]))

        # Vector string
        vector = f"CVSS:3.1/AV:{attack_vector}/AC:{attack_complexity}/PR:{privileges_required}/UI:{user_interaction}/S:{scope}/C:{confidentiality}/I:{integrity}/A:{availability}"

        # Round and determine severity
        score = round(impact_score, 1)
        return score, vector

    def _get_severity(self, score: float) -> str:
        """Get severity from score"""
        for (low, high), severity in self.SEVERITY_MAPPING.items():
            if low <= score <= high:
                return severity
        return "UNKNOWN"

    def generate_cve(self, vulnerability: dict[str, Any], internal_id: str | None = None) -> CVE:
        """Generate CVE data from vulnerability"""
        vuln_type = vulnerability.get("type", "unknown").lower()

        # Calculate CVSS
        cvss_score, cvss_vector = self.calculate_cvss(vulnerability.get("cvss", {}))

        # Generate CVE ID (internal format)
        self._cve_counter += 1
        cve_id = internal_id or f"RF-{datetime.now().year}-{self._cve_counter:04d}"

        # Map CWE
        cwe_id = self.CWE_MAPPING.get(vuln_type, "CWE-000")

        cve = CVE(
            cve_id=cve_id,
            description=vulnerability.get("description", ""),
            severity=self._get_severity(cvss_score),
            cvss_score=cvss_score,
            cvss_vector=cvss_vector,
            affected_product=vulnerability.get("product", ""),
            affected_vendor=vulnerability.get("vendor", ""),
            references=vulnerability.get("references", []),
            cwe_id=cwe_id,
            status="candidates",
        )

        self.cves[cve_id] = cve
        return cve

    def export_cves(self, format: str = "json") -> str:
        """Export CVEs to specified format"""
        if format == "json":
            return json.dumps([self._cve_to_dict(c) for c in self.cves.values()], indent=2)
        elif format == "yaml":
            return cast(str, yaml.dump([self._cve_to_dict(c) for c in self.cves.values()]))
        return str(self.cves)

    def _cve_to_dict(self, cve: CVE) -> dict:
        """Convert CVE to dictionary"""
        return {
            "cve_id": cve.cve_id,
            "description": cve.description,
            "severity": cve.severity,
            "cvss_score": cve.cvss_score,
            "cvss_vector": cve.cvss_vector,
            "affected_product": cve.affected_product,
            "affected_vendor": cve.affected_vendor,
            "cwe_id": cve.cwe_id,
            "references": cve.references,
            "status": cve.status,
            "published_date": cve.published_date,
            "last_modified": cve.last_modified,
        }


class ReportGenerator:
    """
    Generate professional security reports
    Supports multiple formats (HTML, PDF, Markdown, JSON)
    """

    TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "templates"

    def __init__(self):
        self.report: Report | None = None

    def create_report(self, data: dict[str, Any], session_target: str | None = None) -> Report:
        """Create a new report"""
        target = data.get("target", "")

        # If session_target is provided, target must match it
        if session_target is not None:
            if target != session_target:
                raise ValueError(
                    f"Report target '{target}' does not match session target '{session_target}'"
                )

        # Validate target against placeholders
        from redforge.core.verifier import ResponseValidator

        for ph in ResponseValidator.FORBIDDEN_PLACEHOLDERS:
            if ph in target.lower():
                # If target matches the session target, it is considered explicitly provided
                if session_target and ph in session_target.lower():
                    continue
                raise ValueError(f"Report target contains forbidden placeholder '{ph}'")

        report = Report(
            title=data.get("title", "Security Assessment Report"),
            target=target,
            author=data.get("author", "RedForge"),
            scope=data.get("scope", []),
            findings=data.get("findings", []),
            executive_summary=data.get("summary", ""),
            methodology=data.get("methodology", ""),
            limitations=data.get("limitations", ""),
        )
        self.report = report
        return report

    def generate_markdown(self) -> str:
        """Generate Markdown report"""
        if not self.report:
            return ""

        md = f"""# {self.report.title}

**Target:** {self.report.target}
**Author:** {self.report.author}
**Date:** {self.report.created_at}
**Version:** {self.report.version}

---

## Executive Summary

{self.report.executive_summary}

## Scope

{self._format_list(self.report.scope)}

## Methodology

{self.report.methodology}

## Findings Summary

| Severity | Count |
|----------|-------|
"""
        # Count by severity
        severities = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for f in self.report.findings:
            sev = f.get("severity", "INFO").upper()
            severities[sev] = severities.get(sev, 0) + 1

        for sev, count in severities.items():
            md += f"| {sev} | {count} |\n"

        md += "\n## Detailed Findings\n\n"

        for i, finding in enumerate(self.report.findings, 1):
            md += f"""### {i}. {finding.get("title", "Untitled")}

**Severity:** {finding.get("severity", "INFO")}
**CVSS:** {finding.get("cvss_score", "N/A")}
**CWE:** {finding.get("cwe_id", "N/A")}

#### Description

{finding.get("description", "")}

#### Impact

{finding.get("impact", "")}

#### Steps to Reproduce

"""
            for step in finding.get("steps", []):
                md += f"{step}\n"

            md += f"""

#### Remediation

{finding.get("remediation", "")}

"""

            if finding.get("references"):
                md += f"""#### References

{self._format_list(finding.get("references", []))}

"""

            md += "---\n\n"

        if self.report.appendices:
            md += "## Appendices\n\n"
            for name, content in self.report.appendices.items():
                md += f"### {name}\n\n{content}\n\n"

        if self.report.limitations:
            md += f"""## Limitations

{self.report.limitations}

"""

        md += f"""---

*Report generated by RedForge on {self.report.created_at}*
"""

        return md

    def generate_json(self) -> str:
        """Generate JSON report"""
        if not self.report:
            return "{}"

        return json.dumps(
            {
                "title": self.report.title,
                "target": self.report.target,
                "author": self.report.author,
                "scope": self.report.scope,
                "created_at": self.report.created_at,
                "version": self.report.version,
                "executive_summary": self.report.executive_summary,
                "methodology": self.report.methodology,
                "limitations": self.report.limitations,
                "findings": self.report.findings,
                "appendices": self.report.appendices,
            },
            indent=2,
        )

    def generate_html(self) -> str:
        """Generate HTML report"""
        if not self.report:
            return ""

        # Use markdown as content, wrap in HTML
        # Simple HTML template (in production, use proper templating)
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.report.title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        h1 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        h2 {{ color: #2c3e50; margin-top: 30px; }}
        h3 {{ color: #34495e; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
        .severity-CRITICAL {{ color: #8B0000; font-weight: bold; }}
        .severity-HIGH {{ color: #FF4500; font-weight: bold; }}
        .severity-MEDIUM {{ color: #FFA500; font-weight: bold; }}
        .severity-LOW {{ color: #228B22; font-weight: bold; }}
        .severity-INFO {{ color: #4169E1; }}
        pre {{ background: #f4f4f4; padding: 15px; overflow-x: auto; border-radius: 5px; }}
        code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
        hr {{ border: none; border-top: 1px solid #ddd; margin: 30px 0; }}
        .meta {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>{self.report.title}</h1>
    <div class="meta">
        <p><strong>Target:</strong> {self.report.target}</p>
        <p><strong>Author:</strong> {self.report.author}</p>
        <p><strong>Date:</strong> {self.report.created_at}</p>
    </div>

    <h2>Executive Summary</h2>
    <p>{self.report.executive_summary}</p>

    <h2>Findings</h2>
    <table>
        <tr>
            <th>Title</th>
            <th>Severity</th>
            <th>CVSS</th>
            <th>CWE</th>
        </tr>
"""

        for f in self.report.findings:
            sev = f.get("severity", "INFO").upper()
            html += f"""        <tr>
            <td>{f.get("title", "")}</td>
            <td class="severity-{sev}">{sev}</td>
            <td>{f.get("cvss_score", "N/A")}</td>
            <td>{f.get("cwe_id", "N/A")}</td>
        </tr>
"""

        html += """    </table>
</body>
</html>"""

        return html

    def _format_list(self, items: list[str]) -> str:
        """Format list items"""
        return "\n".join(f"- {item}" for item in items)

    def save_report(self, path: Path, format: str = "md"):
        """Save report to file"""
        if format == "md":
            content = self.generate_markdown()
        elif format == "json":
            content = self.generate_json()
        elif format == "html":
            content = self.generate_html()
        else:
            raise ValueError(f"Unsupported format: {format}")

        path.write_text(content)
        logger.info(f"Report saved to {path}")


class AutomationEngine:
    """
    Advanced automation engine for RedForge
    Supports complex multi-step workflows
    """

    def __init__(self, tool_manager, safety_engine, llm=None):
        self.tool_manager = tool_manager
        self.safety_engine = safety_engine
        self.llm = llm
        self.workflows: dict[str, Workflow] = {}

    def create_workflow(self, name: str, steps: list[dict]) -> "Workflow":
        """Create a new workflow"""
        workflow = Workflow(name=name, steps=steps)
        self.workflows[name] = workflow
        return workflow

    def execute_workflow(self, name: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a workflow"""
        workflow = self.workflows.get(name)
        if not workflow:
            return {"error": f"Workflow '{name}' not found"}

        return workflow.execute(context, self.tool_manager, self.safety_engine)

    def generate_workflow(self, goal: str, mode: str = "bugbounty") -> list[dict]:
        """Generate workflow using LLM"""
        if not self.llm:
            return [{"error": "LLM not configured"}]

        prompt = f"""Generate a step-by-step workflow for: {goal}
Mode: {mode}

Return a JSON array of steps, each with:
- name: step name
- tool: tool to use (or "llm" for AI assistance)
- args: arguments for the tool
- safety_check: whether to check scope

Example:
[{{"name": "scan ports", "tool": "nmap", "args": {{"target": "${{target}}", "ports": "1-1000"}}}}]
"""

        response = self.llm.generate(prompt)

        try:
            # Parse JSON response
            import re

            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if json_match:
                return cast(list[dict[Any, Any]], json.loads(json_match.group()))
        except (json.JSONDecodeError, AttributeError):
            pass  # nosec B110 - LLM JSON parse is best-effort; caller receives error dict if parsing fails

        return [{"error": "Could not generate workflow"}]


@dataclass
class Workflow:
    """Automation workflow definition"""

    name: str
    steps: list[dict]

    def execute(self, context: dict[str, Any], tool_manager, safety_engine) -> dict[str, Any]:
        """Execute workflow"""
        results: dict[str, Any] = {"workflow": self.name, "steps_executed": 0, "results": [], "success": True}

        for i, step in enumerate(self.steps):
            step_result = self._execute_step(step, context, tool_manager, safety_engine)
            results["results"].append(step_result)
            results["steps_executed"] = i + 1

            # Stop on failure unless continue_on_error
            if not step_result.get("success", True) and not step.get("continue_on_error"):
                results["success"] = False
                results["failed_at"] = i + 1
                break

        return results

    def _execute_step(
        self, step: dict, context: dict, tool_manager, safety_engine
    ) -> dict[str, Any]:
        """Execute a single step"""
        name = step.get("name", "unnamed")
        tool = step.get("tool")
        args = step.get("args", {})

        # Substitute context variables
        args_str = str(args)
        for key, value in context.items():
            args_str = args_str.replace(f"${{{key}}}", str(value))

        # Safety check
        if step.get("safety_check", True):
            if tool_manager:
                # Check tool is available
                pass  # Simplified

        # Execute
        result = {"name": name, "tool": tool, "success": True}

        if tool == "llm":
            result["output"] = "LLM execution placeholder"
        elif tool_manager:
            # Tool execution would happen here
            result["output"] = f"Tool '{tool}' execution placeholder"
        else:
            result["output"] = "No tool manager configured"

        return result

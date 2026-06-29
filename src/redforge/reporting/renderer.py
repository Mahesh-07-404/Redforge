from .contracts import SynthesisReport
from .templates import ReportTemplates

class ReportRenderer:
    @staticmethod
    def render_to_markdown(report: SynthesisReport) -> str:
        exec_summary = (
            f"**Scope:** {report.executive_summary.scope}\n"
            f"**Methodology:** {report.executive_summary.methodology}\n"
            f"**Conclusion:** {report.executive_summary.conclusion}"
        )
        
        findings_summary = ""
        findings_details = ""
        for f in report.findings:
            findings_summary += f"- **[{f.severity}]** {f.title} (Affected: {', '.join(f.affected_assets)})\n"
            findings_details += (
                f"### {f.title} ({f.severity})\n"
                f"- **Description:** {f.description}\n"
                f"- **Remediation:** {f.remediation}\n\n"
            )
            
        timeline_str = ""
        for t in report.timeline:
            timeline_str += f"- {t}\n"
            
        return ReportTemplates.MARKDOWN_TEMPLATE.format(
            executive_summary=exec_summary,
            findings_summary=findings_summary,
            timeline=timeline_str,
            findings_details=findings_details
        )

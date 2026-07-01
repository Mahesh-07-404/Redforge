import json

from .contracts import SynthesisReport
from .renderer import ReportRenderer


class ReportExporter:
    @staticmethod
    def export_json(report: SynthesisReport) -> str:
        return report.model_dump_json(indent=2)

    @staticmethod
    def export_markdown(report: SynthesisReport) -> str:
        return ReportRenderer.render_to_markdown(report)

    @staticmethod
    def export_sarif(report: SynthesisReport) -> str:
        sarif = {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {"driver": {"name": "RedForge", "version": "2.0.0"}},
                    "results": [
                        {
                            "ruleId": f.cve or f.id,
                            "message": {"text": f.description},
                            "level": "error" if f.severity in ("Critical", "High") else "warning",
                        }
                        for f in report.findings
                    ],
                }
            ],
        }
        return json.dumps(sarif, indent=2)

from typing import List
from ..contracts.report import Finding

class ReportFormatter:
    def to_markdown(self, findings: List[Finding]) -> str:
        return "# Report\\n" + "\\n".join([f"- {f.title}: {f.description}" for f in findings])

    def to_json(self, findings: List[Finding]) -> str:
        import json
        return json.dumps([f.model_dump() for f in findings])

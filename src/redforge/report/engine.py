from typing import List
from .collector import ReportCollector
from .formatter import ReportFormatter
from ..contracts.tool import VerifiedResult
from ..contracts.report import Finding

class ReportEngine:
    def __init__(self):
        self.collector = ReportCollector()
        self.formatter = ReportFormatter()

    def add_finding(self, verified_result: VerifiedResult, session_id: str):
        self.collector.add_from_verified(verified_result, session_id)

    def get_findings(self, session_id: str) -> List[Finding]:
        return [f for f in self.collector.findings if f.session_id == session_id]

    def generate(self, session_id: str, format: str = "markdown") -> str:
        findings = self.get_findings(session_id)
        if format == "json":
            return self.formatter.to_json(findings)
        return self.formatter.to_markdown(findings)

from typing import List
from ..contracts.report import Finding
from ..contracts.tool import VerifiedResult

class ReportCollector:
    def __init__(self):
        self.findings: List[Finding] = []

    def add_from_verified(self, verified_result: VerifiedResult, session_id: str):
        pass

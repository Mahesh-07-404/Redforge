from typing import Any

from .contracts import SynthesisReport
from .correlation import CorrelationEngine
from .deduplicator import Deduplicator
from .synthesizer import KnowledgeSynthesizer


class ReportingEngine:
    @staticmethod
    def generate_report(
        session_id: str,
        execution_id: str,
        target: str,
        raw_evidence: list[dict[str, Any]],
        entities: list[Any],
        world_state_findings: list[str],
    ) -> SynthesisReport:
        report = KnowledgeSynthesizer.synthesize(
            session_id=session_id,
            execution_id=execution_id,
            target=target,
            raw_evidence=raw_evidence,
            entities=entities,
            world_state_findings=world_state_findings,
        )

        report.findings = CorrelationEngine.correlate_findings(report.findings)
        report.findings = Deduplicator.deduplicate(report.findings)
        return report

from typing import List, Dict, Any
from .contracts import SynthesisReport
from .synthesizer import KnowledgeSynthesizer
from .correlation import CorrelationEngine
from .deduplicator import Deduplicator

class ReportingEngine:
    @staticmethod
    def generate_report(
        session_id: str,
        execution_id: str,
        target: str,
        raw_evidence: List[Dict[str, Any]],
        entities: List[Any],
        world_state_findings: List[str]
    ) -> SynthesisReport:
        report = KnowledgeSynthesizer.synthesize(
            session_id=session_id,
            execution_id=execution_id,
            target=target,
            raw_evidence=raw_evidence,
            entities=entities,
            world_state_findings=world_state_findings
        )
        
        report.findings = CorrelationEngine.correlate_findings(report.findings)
        report.findings = Deduplicator.deduplicate(report.findings)
        return report

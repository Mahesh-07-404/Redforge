import pytest
import json
from redforge.reporting.contracts import Finding, ExecutiveSummary, SynthesisReport
from redforge.reporting.risk import RiskEngine
from redforge.reporting.remediation import RemediationEngine
from redforge.reporting.correlation import CorrelationEngine
from redforge.reporting.deduplicator import Deduplicator
from redforge.reporting.timeline import ReportTimelineGenerator
from redforge.reporting.renderer import ReportRenderer
from redforge.reporting.exporter import ReportExporter
from redforge.reporting.engine import ReportingEngine

def test_risk_scoring():
    # Technical risk = (likelihood + exploitability) / 2 = 9.0
    # Business risk = impact = 8.0
    # Combined = 8.5 (Critical)
    score = RiskEngine.calculate_risk(likelihood=10.0, impact=8.0, exploitability=8.0, confidence=0.9)
    assert score.overall_risk == "Critical"
    assert score.technical_risk == 9.0
    assert score.business_risk == 8.0

def test_remediation_engine():
    rem = RemediationEngine.get_remediation("CVE-2026-9999")
    assert "Upgrade package" in rem["fix"]
    assert "CVE-2026-9999" in rem["references"][0]

def test_deduplicator_and_correlation():
    f1 = Finding(id="1", title="SQL Injection", description="desc", severity="High", confidence=0.9, cve="CVE-1", affected_assets=["a1"])
    f2 = Finding(id="2", title="SQL Injection", description="desc", severity="High", confidence=0.9, cve="CVE-1", affected_assets=["a2"])
    
    # 1. Correlation
    correlated = CorrelationEngine.correlate_findings([f1, f2])
    assert len(correlated) == 1
    assert "a1" in correlated[0].affected_assets
    assert "a2" in correlated[0].affected_assets
    
    # 2. Deduplication
    deduped = Deduplicator.deduplicate([f1, f2])
    assert len(deduped) == 1

def test_timeline_generator():
    steps = ["Scan", "Verify", "Done"]
    timeline = ReportTimelineGenerator.generate_timeline(steps)
    assert len(timeline) == 3
    assert timeline[0] == "Milestone: Scan"

def test_rendering_and_exporting():
    exec_summary = ExecutiveSummary(
        scope="Scope description",
        objectives="Objectives",
        methodology="Methodology details",
        key_findings="None",
        risk_summary="Low",
        recommendations="Patch everything",
        conclusion="Pass"
    )
    
    finding = Finding(
        id="f1",
        title="Insecure service configuration",
        description="desc",
        severity="Medium",
        confidence=0.8,
        affected_assets=["target.local"],
        remediation="Update config."
    )
    
    report = SynthesisReport(
        session_id="s1",
        execution_id="e1",
        target="target.local",
        executive_summary=exec_summary,
        findings=[finding],
        timeline=["Start", "Finish"]
    )
    
    # 1. Render Markdown
    md_out = ReportRenderer.render_to_markdown(report)
    assert "# Security Assessment Report" in md_out
    assert "Scope description" in md_out
    
    # 2. Export formats
    json_out = ReportExporter.export_json(report)
    assert json.loads(json_out)["session_id"] == "s1"
    
    sarif_out = ReportExporter.export_sarif(report)
    sarif_obj = json.loads(sarif_out)
    assert sarif_obj["version"] == "2.1.0"
    assert len(sarif_obj["runs"][0]["results"]) == 1

def test_reporting_engine():
    report = ReportingEngine.generate_report(
        session_id="s1",
        execution_id="e1",
        target="example.com",
        raw_evidence=[],
        entities=[],
        world_state_findings=["Vulnerability check", "SSL cert expiry check"]
    )
    assert report.target == "example.com"
    assert len(report.findings) == 2

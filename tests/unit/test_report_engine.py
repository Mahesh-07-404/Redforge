import pytest
from redforge.reports.engine import ReportEngine
from redforge.contracts.tool import VerifiedResult, ToolResult, VerificationStatus
from datetime import datetime

def test_report_engine():
    engine = ReportEngine()
    
    tr = ToolResult(
        tool_name="test", command=["test"], exit_code=0, stdout="ok",
        stderr="", parsed_output={}, execution_time_ms=10, timed_out=False, error=None
    )
    vr = VerifiedResult(
        tool_result=tr, status=VerificationStatus.PASSED, verified_at=datetime.now(),
        facts=["ok"], anomalies=[]
    )
    
    engine.add_finding(vr, "123")
    assert isinstance(engine.generate("123"), str)

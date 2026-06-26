import pytest
from redforge.core.verifier import Verifier
from redforge.contracts.tool import ToolResult
from redforge.contracts.session import SessionState
from datetime import datetime

def test_verifier_passes():
    verifier = Verifier()
    tr = ToolResult(
        tool_name="test",
        command=["test", "localhost"],
        exit_code=0,
        stdout="ok",
        stderr="",
        parsed_output={},
        execution_time_ms=10,
        timed_out=False,
        error=None
    )
    ss = SessionState(
        id="123", mode="bugbounty", target="localhost", autonomy="manual",
        created_at=datetime.now(), updated_at=datetime.now(), status="active"
    )
    
    vr = verifier.validate(tr, ss)
    assert vr.status.value == "passed"

import pytest
from redforge.tools.executor import ToolExecutor
from redforge.contracts.tool import ToolCall
from redforge.contracts.intent import RiskLevel

def test_tool_executor_denies_unapproved():
    executor = ToolExecutor()
    call = ToolCall(
        tool_name="nmap",
        command=["nmap", "localhost"],
        target="localhost",
        timeout_seconds=5,
        risk_level=RiskLevel.MEDIUM,
        session_id="123",
        approved=False
    )
    result = executor.execute(call)
    assert result.exit_code == -1
    assert "Execution denied" in str(result.error)

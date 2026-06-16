from datetime import datetime
from typing import List
from .output_validator import OutputValidator
from .scope_checker import ScopeChecker
from .hallucination_guard import HallucinationGuard
from ..contracts.tool import ToolResult, VerifiedResult, VerificationStatus
from ..contracts.session import SessionState

class Verifier:
    def __init__(self):
        self.output_validator = OutputValidator()
        self.scope_checker = ScopeChecker()
        self.guard = HallucinationGuard()

    def validate(self, tool_result: ToolResult, session_state: SessionState) -> VerifiedResult:
        if session_state.target and session_state.target not in str(tool_result.command):
            return VerifiedResult(
                tool_result=tool_result,
                status=VerificationStatus.FAILED_SCOPE,
                verified_at=datetime.now(),
                facts=[],
                anomalies=["Target not in command"]
            )
            
        if not self.output_validator.validate(tool_result):
            return VerifiedResult(
                tool_result=tool_result,
                status=VerificationStatus.FAILED_ERROR,
                verified_at=datetime.now(),
                facts=[],
                anomalies=["Output validation failed or non-zero exit code"]
            )
            
        return VerifiedResult(
            tool_result=tool_result,
            status=VerificationStatus.PASSED,
            verified_at=datetime.now(),
            facts=["Execution succeeded"],
            anomalies=[]
        )

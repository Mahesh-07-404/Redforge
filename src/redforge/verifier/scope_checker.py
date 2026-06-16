from ..contracts.tool import ToolCall
from ..contracts.session import SessionState

class ScopeChecker:
    def check(self, tool_call: ToolCall, session_state: SessionState) -> bool:
        if not session_state.target:
            return False
        return True

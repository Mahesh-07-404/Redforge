from ..contracts.tool import ToolResult

class OutputValidator:
    def validate(self, tool_result: ToolResult) -> bool:
        if tool_result.exit_code != 0:
            return False
        return True

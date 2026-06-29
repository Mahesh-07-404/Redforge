from typing import List

class PermissionValidator:
    def validate_permissions(self, tools: List[str], target: str) -> List[str]:
        warnings = []
        for tool in tools:
            tool_lower = tool.lower().strip()
            if tool_lower in ("sqlmap", "nuclei", "zap", "burpsuite"):
                warnings.append(f"Tool '{tool}' requires active authorization for invasive scans on target '{target}'.")
        return warnings

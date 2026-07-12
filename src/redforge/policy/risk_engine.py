from .policy_decision import RiskLevel
from .policy_rules import PolicyRules


class RiskEngine:
    def calculate_risk(self, tools: list[str]) -> RiskLevel:
        if not tools:
            return RiskLevel.LOW

        highest_risk = RiskLevel.LOW
        risk_hierarchy = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4,
        }

        for tool_name in tools:
            tool_lower = tool_name.lower().strip()
            level_str = PolicyRules.TOOL_RISK_MAP.get(tool_lower, "LOW")
            level = RiskLevel[level_str]
            if risk_hierarchy[level] > risk_hierarchy[highest_risk]:
                highest_risk = level

        return highest_risk

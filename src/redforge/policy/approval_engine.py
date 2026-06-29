from .policy_decision import DecisionStatus, RiskLevel

class ApprovalEngine:
    def evaluate(self, risk_level: RiskLevel, scope_errors: list) -> DecisionStatus:
        if scope_errors:
            return DecisionStatus.DENY
            
        if risk_level == RiskLevel.LOW:
            return DecisionStatus.ALLOW
        else:
            return DecisionStatus.REQUIRES_APPROVAL

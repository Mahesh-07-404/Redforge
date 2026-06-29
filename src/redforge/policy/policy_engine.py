from typing import List, Optional
from .policy_decision import PolicyDecision, DecisionStatus, RiskLevel
from .scope_validator import ScopeValidator
from .risk_engine import RiskEngine
from .approval_engine import ApprovalEngine
from .permission_validator import PermissionValidator
from ..planner.plan import Plan

class PolicyEngine:
    def __init__(self):
        self.scope_validator = ScopeValidator()
        self.risk_engine = RiskEngine()
        self.approval_engine = ApprovalEngine()
        self.permission_validator = PermissionValidator()

    def evaluate_plan(self, plan: Plan, target: str) -> PolicyDecision:
        scope_errors = self.scope_validator.validate_target(target)
        
        tools = plan.required_tools or [t.tool_hint for t in plan.ordered_tasks if t.tool_hint]
        tools = [t for t in tools if t]
        
        risk_level = self.risk_engine.calculate_risk(tools)
        status = self.approval_engine.evaluate(risk_level, scope_errors)
        
        warnings = []
        if scope_errors:
            warnings.extend(scope_errors)
            
        permission_warnings = self.permission_validator.validate_permissions(tools, target)
        warnings.extend(permission_warnings)
        
        reason = None
        if status == DecisionStatus.DENY:
            reason = f"Execution blocked due to scope violations: {'; '.join(scope_errors)}"
        elif status == DecisionStatus.REQUIRES_APPROVAL:
            reason = f"Execution requires confirmation due to {risk_level.value} risk level."
        else:
            reason = "Execution automatically allowed (LOW risk)."
            
        return PolicyDecision(
            status=status,
            risk_level=risk_level,
            reason=reason,
            warnings=warnings,
            required_permissions=tools
        )

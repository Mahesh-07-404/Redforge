import pytest
from redforge.policy.policy_decision import DecisionStatus, RiskLevel, PolicyDecision
from redforge.policy.policy_rules import PolicyRules
from redforge.policy.scope_validator import ScopeValidator
from redforge.policy.risk_engine import RiskEngine
from redforge.policy.permission_validator import PermissionValidator
from redforge.policy.approval_engine import ApprovalEngine
from redforge.policy.policy_engine import PolicyEngine
from redforge.planner.plan import Plan
from redforge.planner.task import Task

def test_scope_validator():
    validator = ScopeValidator()
    
    # Prohibited target
    errors = validator.validate_target("127.0.0.1")
    assert len(errors) > 0
    assert any("prohibited" in e for e in errors)
    
    errors = validator.validate_target("localhost")
    assert len(errors) > 0
    
    # Invalid target
    errors = validator.validate_target("invalid_target_no_dot")
    assert len(errors) > 0
    assert any("not a valid" in e for e in errors)
    
    # Valid target
    errors = validator.validate_target("example.com")
    assert not errors

def test_risk_engine():
    engine = RiskEngine()
    
    # Low risk
    assert engine.calculate_risk(["subfinder", "httpx"]) == RiskLevel.LOW
    
    # Medium risk
    assert engine.calculate_risk(["subfinder", "nmap"]) == RiskLevel.MEDIUM
    
    # High risk
    assert engine.calculate_risk(["nuclei", "zap"]) == RiskLevel.HIGH
    
    # Critical risk
    assert engine.calculate_risk(["sqlmap"]) == RiskLevel.CRITICAL

def test_permission_validator():
    validator = PermissionValidator()
    
    warnings = validator.validate_permissions(["sqlmap", "subfinder"], "example.com")
    assert len(warnings) == 1
    assert "sqlmap" in warnings[0]

def test_approval_engine():
    engine = ApprovalEngine()
    
    # Auto-approve low risk
    assert engine.evaluate(RiskLevel.LOW, []) == DecisionStatus.ALLOW
    
    # Requires approval for medium/high/critical
    assert engine.evaluate(RiskLevel.MEDIUM, []) == DecisionStatus.REQUIRES_APPROVAL
    assert engine.evaluate(RiskLevel.HIGH, []) == DecisionStatus.REQUIRES_APPROVAL
    assert engine.evaluate(RiskLevel.CRITICAL, []) == DecisionStatus.REQUIRES_APPROVAL
    
    # Scope violation leads to Deny
    assert engine.evaluate(RiskLevel.LOW, ["Scope violation"]) == DecisionStatus.DENY

def test_policy_engine_evaluation():
    engine = PolicyEngine()
    
    # Construct Plan
    plan = Plan(
        goal="Test passive scanning",
        ordered_tasks=[
            Task(id="subfinder", title="Subfinder", description="Enum", tool_hint="subfinder"),
            Task(id="httpx", title="HTTPX", description="Probe", tool_hint="httpx")
        ],
        required_tools=["subfinder", "httpx"]
    )
    
    # Evaluate valid target
    decision = engine.evaluate_plan(plan, "example.com")
    assert decision.status == DecisionStatus.ALLOW
    assert decision.risk_level == RiskLevel.LOW
    assert not decision.warnings
    
    # Evaluate prohibited target
    decision_prohibited = engine.evaluate_plan(plan, "127.0.0.1")
    assert decision_prohibited.status == DecisionStatus.DENY
    assert len(decision_prohibited.warnings) > 0
    
    # Evaluate critical risk tool
    plan_invasive = Plan(
        goal="Exploit target",
        ordered_tasks=[
            Task(id="sqlmap", title="SQLMap", description="Exploit", tool_hint="sqlmap")
        ],
        required_tools=["sqlmap"]
    )
    decision_invasive = engine.evaluate_plan(plan_invasive, "example.com")
    assert decision_invasive.status == DecisionStatus.REQUIRES_APPROVAL
    assert decision_invasive.risk_level == RiskLevel.CRITICAL
    assert len(decision_invasive.warnings) == 1

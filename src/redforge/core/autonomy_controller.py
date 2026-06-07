"""Autonomy controller for managing agent action permissions"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class AutonomyLevel(Enum):
    MANUAL = "manual"
    PARTIAL = "partial"
    FULL = "full"


class ActionRisk(Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Action:
    name: str
    description: str
    risk_level: ActionRisk
    requires_confirmation: bool = False
    can_auto_execute: bool = False
    destructive: bool = False
    irreversible: bool = False


@dataclass
class AutonomyDecision:
    allowed: bool
    action: Action
    reason: str
    requires_confirmation: bool
    confirmation_message: Optional[str] = None


class AutonomyController:
    """Controls agent autonomy and action permissions"""
    
    SAFE_ACTIONS = {
        "read", "list", "search", "get", "show", "display",
        "view", "check", "status", "info", "help", "analyze",
        "scan_readonly", "gather_info"
    }
    
    DESTRUCTIVE_KEYWORDS = {
        "delete", "drop", "remove", "rm", "wipe", "format",
        "destroy", "exploit", "attack", "inject", "exfiltrate"
    }
    
    IRREVERSIBLE_KEYWORDS = {
        "delete", "drop", "truncate", "wipe", "destroy",
        "overwrite", "corrupt", "modify_critical"
    }
    
    def __init__(
        self,
        default_level: AutonomyLevel = AutonomyLevel.MANUAL,
        max_level: AutonomyLevel = AutonomyLevel.PARTIAL,
        consent_required: bool = True,
        destructive_threshold: int = 3
    ):
        self.default_level = default_level
        self.max_level = max_level
        self.consent_required = consent_required
        self.destructive_threshold = destructive_threshold
        
        self.current_level = default_level
        self.destructive_action_count = 0
        self.action_log: List[Dict[str, Any]] = []
        self.consent_given = False
        self.consent_timestamp: Optional[datetime] = None
    
    def set_level(self, level: AutonomyLevel) -> bool:
        """Set autonomy level with validation"""
        if level.value == "full" and not self.consent_given:
            if self.consent_required:
                return False
        
        if level == AutonomyLevel.FULL and self.max_level != AutonomyLevel.FULL:
            return False
        
        self.current_level = level
        return True
    
    def give_consent(self, level: AutonomyLevel = AutonomyLevel.FULL) -> None:
        """Record user consent for higher autonomy"""
        self.consent_given = True
        self.consent_timestamp = datetime.now()
        if level == AutonomyLevel.FULL:
            self.current_level = AutonomyLevel.FULL
        
        self._log_action("consent", f"Consent given for {level.value} autonomy")
    
    def revoke_consent(self) -> None:
        """Revoke consent and drop to manual mode"""
        self.consent_given = False
        self.consent_timestamp = None
        self.current_level = AutonomyLevel.MANUAL
        self._log_action("consent_revoke", "Consent revoked")
    
    def assess_action_risk(self, action_name: str, action_args: Optional[Dict] = None) -> ActionRisk:
        """Assess the risk level of an action"""
        action_lower = action_name.lower()
        
        if any(kw in action_lower for kw in self.DESTRUCTIVE_KEYWORDS):
            if any(kw in action_lower for kw in self.IRREVERSIBLE_KEYWORDS):
                return ActionRisk.CRITICAL
            return ActionRisk.HIGH
        
        if any(kw in action_lower for kw in ["modify", "change", "update", "write", "create"]):
            return ActionRisk.MEDIUM
        
        if any(kw in action_lower for kw in self.SAFE_ACTIONS):
            return ActionRisk.SAFE
        
        return ActionRisk.LOW
    
    def should_confirm_action(
        self,
        action_name: str,
        action_args: Optional[Dict] = None
    ) -> bool:
        """Determine if an action requires confirmation"""
        if self.current_level == AutonomyLevel.FULL:
            return False
        
        risk = self.assess_action_risk(action_name, action_args)
        
        if risk in [ActionRisk.HIGH, ActionRisk.CRITICAL]:
            return True
        
        if self.current_level == AutonomyLevel.PARTIAL:
            return risk in [ActionRisk.MEDIUM, ActionRisk.HIGH, ActionRisk.CRITICAL]
        
        return True
    
    def evaluate_action(
        self,
        action_name: str,
        action_description: str = "",
        action_args: Optional[Dict] = None
    ) -> AutonomyDecision:
        """Evaluate if an action should be allowed"""
        risk = self.assess_action_risk(action_name, action_args)
        requires_confirmation = self.should_confirm_action(action_name, action_args)
        
        action = Action(
            name=action_name,
            description=action_description,
            risk_level=risk,
            requires_confirmation=requires_confirmation,
            can_auto_execute=not requires_confirmation and self.current_level != AutonomyLevel.MANUAL,
            destructive=risk in [ActionRisk.HIGH, ActionRisk.CRITICAL],
            irreversible=risk == ActionRisk.CRITICAL
        )
        
        if self.current_level == AutonomyLevel.MANUAL:
            if risk in [ActionRisk.HIGH, ActionRisk.CRITICAL]:
                return AutonomyDecision(
                    allowed=False,
                    action=action,
                    reason=f"Action {action_name} requires confirmation in MANUAL mode",
                    requires_confirmation=True,
                    confirmation_message=f"This action ({action_name}) is {risk.value} risk. Do you want to proceed?"
                )
            elif requires_confirmation:
                return AutonomyDecision(
                    allowed=True,
                    action=action,
                    reason=f"Action requires confirmation in MANUAL mode",
                    requires_confirmation=True,
                    confirmation_message=f"Confirm action: {action_name}"
                )
            else:
                return AutonomyDecision(
                    allowed=True,
                    action=action,
                    reason="Safe action, allowed with confirmation",
                    requires_confirmation=True,
                    confirmation_message=f"Confirm: {action_name}"
                )
        
        elif self.current_level == AutonomyLevel.PARTIAL:
            if risk in [ActionRisk.HIGH, ActionRisk.CRITICAL]:
                return AutonomyDecision(
                    allowed=True,
                    action=action,
                    reason=f"Action allowed in PARTIAL mode with confirmation",
                    requires_confirmation=True,
                    confirmation_message=f"⚠️ {risk.value.upper()} risk action: {action_name}. Proceed?"
                )
            
            if risk == ActionRisk.MEDIUM:
                return AutonomyDecision(
                    allowed=True,
                    action=action,
                    reason="Medium risk, allowed in PARTIAL mode",
                    requires_confirmation=True,
                    confirmation_message=f"Confirm medium-risk action: {action_name}"
                )
            
            return AutonomyDecision(
                allowed=True,
                action=action,
                reason="Low/safe action, auto-executed in PARTIAL mode",
                requires_confirmation=False
            )
        
        else:
            if risk == ActionRisk.CRITICAL:
                return AutonomyDecision(
                    allowed=True,
                    action=action,
                    reason="CRITICAL action allowed in FULL mode",
                    requires_confirmation=True,
                    confirmation_message=f"⚠️ CRITICAL: {action_name}"
                )
            
            return AutonomyDecision(
                allowed=True,
                action=action,
                reason="FULL autonomy - no restrictions",
                requires_confirmation=risk in [ActionRisk.HIGH, ActionRisk.CRITICAL]
            )
    
    def confirm_action(self, action_name: str) -> bool:
        """Record that user confirmed an action"""
        self._log_action("confirmed", action_name)
        
        risk = self.assess_action_risk(action_name)
        if risk in [ActionRisk.HIGH, ActionRisk.CRITICAL]:
            self.destructive_action_count += 1
            
            if self.destructive_action_count >= self.destructive_threshold:
                self._log_action("auto_demote", "Auto-demoted to PARTIAL due to destructive actions")
                self.current_level = AutonomyLevel.PARTIAL
        
        return True
    
    def _log_action(self, action_type: str, description: str) -> None:
        """Log an action for audit"""
        self.action_log.append({
            "type": action_type,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "autonomy_level": self.current_level.value
        })
    
    def get_status(self) -> Dict[str, Any]:
        """Get current autonomy status"""
        return {
            "current_level": self.current_level.value,
            "max_level": self.max_level.value,
            "consent_given": self.consent_given,
            "consent_timestamp": self.consent_timestamp.isoformat() if self.consent_timestamp else None,
            "destructive_count": self.destructive_action_count,
            "action_log_size": len(self.action_log),
            "requires_consent_for_full": self.consent_required
        }
    
    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent action log entries"""
        return self.action_log[-limit:]

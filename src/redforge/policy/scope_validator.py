from typing import List
from .policy_rules import PolicyRules

class ScopeValidator:
    def validate_target(self, target: str) -> List[str]:
        errors = []
        if not target:
            errors.append("Target is empty.")
            return errors
            
        t_lower = target.lower().strip()
        for p in PolicyRules.PROHIBITED_TARGETS:
            if p in t_lower:
                errors.append(f"Target '{target}' contains prohibited domain/IP '{p}'.")
                
        if "." not in t_lower and t_lower not in ["localhost"]:
            errors.append(f"Target '{target}' is not a valid domain or IP.")
            
        return errors

from typing import Any


class ConditionValidator:
    @staticmethod
    def check_conditions(conditions: list[str], context: dict[str, Any]) -> bool:
        for condition in conditions:
            if condition == "target_reachable" and not context.get("target_reachable", True):
                return False
        return True

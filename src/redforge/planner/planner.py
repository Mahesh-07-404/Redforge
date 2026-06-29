from typing import List, Optional
from .planner_context import PlannerContext
from .plan import Plan
from .validators import PlannerValidator
from .strategy import (
    PlanningStrategy, PassiveReconStrategy, WebEnumerationStrategy,
    BugBountyStrategy, CTFStrategy, LearningStrategy, ReportStrategy
)

class Planner:
    def __init__(self, strategies: Optional[List[PlanningStrategy]] = None):
        self.validator = PlannerValidator()
        if strategies is None:
            self.strategies = [
                PassiveReconStrategy(),
                WebEnumerationStrategy(),
                BugBountyStrategy(),
                CTFStrategy(),
                LearningStrategy(),
                ReportStrategy()
            ]
        else:
            self.strategies = strategies

    def create_plan(self, context: PlannerContext) -> Plan:
        # 1. Validate
        errors = self.validator.validate(context)
        if errors:
            raise ValueError("; ".join(errors))

        # 2. Select strategy
        selected_strategy = None
        for strategy in self.strategies:
            if strategy.can_handle(context):
                selected_strategy = strategy
                break

        if not selected_strategy:
            raise ValueError("No planning strategy found for the current context.")

        # 3. Generate Plan
        return selected_strategy.create_plan(context)

from .contracts import ReasoningDecision
from .self_evaluator import SelfEvaluator
from .world_state import WorldState


class Reasoner:
    def __init__(self):
        self.world_state = WorldState()

    def think(self, goal_text: str) -> ReasoningDecision:
        progress = SelfEvaluator.evaluate_progress(self.world_state, goal_text)
        if progress["completed"]:
            return ReasoningDecision(action="stop", reason="Goal conditions met successfully.")
        return ReasoningDecision(
            action="execute", reason="Goal incomplete. Proceed with task plans."
        )

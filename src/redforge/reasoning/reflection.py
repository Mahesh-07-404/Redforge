from .contracts import ReasoningDecision
from .world_state import WorldState


class SelfReflection:
    @staticmethod
    def reflect(task_id: str, success: bool, world_state: WorldState) -> ReasoningDecision:
        if not success:
            return ReasoningDecision(
                action="replan",
                reason=f"Task {task_id} failed. Need to trigger fallback/replanning.",
                next_task_id=task_id,
            )

        if task_id == "subfinder" and not world_state.hosts:
            return ReasoningDecision(
                action="replan",
                reason="Subfinder returned no subdomains. Re-routing to amass search.",
                next_task_id="amass",
            )

        return ReasoningDecision(
            action="execute",
            reason=f"Task {task_id} succeeded. Proceed with normal execution path.",
        )

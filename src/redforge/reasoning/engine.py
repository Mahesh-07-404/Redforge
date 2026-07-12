import logging

from ..planner.task import Task
from .failure_handler import FailureHandler
from .goal_manager import GoalManager
from .reasoner import Reasoner
from .state_machine import ReasoningState, ReasoningStateMachine
from .strategy_selector import StrategySelector
from .task_decomposer import TaskDecomposer

logger = logging.getLogger(__name__)


class ReasoningEngine:
    def __init__(self):
        self.state_machine = ReasoningStateMachine()
        self.goal_manager = GoalManager()
        self.reasoner = Reasoner()
        self.failure_handler = FailureHandler()

    def process_goal(self, goal_text: str) -> list[Task]:
        self.state_machine.transition_to(ReasoningState.PLANNING)
        self.goal_manager.create_goal(goal_text)
        StrategySelector.select_strategy(goal_text)

        tasks = TaskDecomposer.decompose(goal_text)
        self.state_machine.transition_to(ReasoningState.REASONING)
        return tasks

    def reason(self, goal: str, context: dict | None = None, session_id: str = "") -> dict:
        # Retrieve and render the reasoning prompt template automatically
        from redforge.prompt_library.registry import get_prompt_library_registry
        from redforge.prompts.registry import get_prompt_registry

        try:
            registry = get_prompt_registry()
            rendered = registry.render(
                "reasoning_thought_loop", query=goal, context=str(context or {})
            )
            logger.debug("Rendered reasoning thought loop prompt:\n%s", rendered)
        except Exception as e:
            logger.debug("Failed to render reasoning prompt: %s", e)

        try:
            lib_registry = get_prompt_library_registry()
            rendered_gen = lib_registry.render(
                "reasoning_critical_thought", problem_statement=goal, known_facts=str(context or {})
            )
            logger.debug("Rendered critical thought reasoning prompt:\n%s", rendered_gen)
        except Exception as e:
            logger.debug("Failed to render critical reasoning prompt: %s", e)

        decision_obj = self.reasoner.think(goal)
        return {
            "decision": decision_obj.reason,
            "action": decision_obj.action,
            "strategy": decision_obj.strategy or "Default",
            "confidence": 0.9,
            "next_actions": [decision_obj.next_task_id] if decision_obj.next_task_id else [],
        }

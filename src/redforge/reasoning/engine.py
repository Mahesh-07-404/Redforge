from typing import List
from .state_machine import ReasoningStateMachine, ReasoningState
from .goal_manager import GoalManager
from .task_decomposer import TaskDecomposer
from .strategy_selector import StrategySelector
from .reasoner import Reasoner
from .self_evaluator import SelfEvaluator
from .reflection import SelfReflection
from .replanner import Replanner
from .failure_handler import FailureHandler
from ..planner.task import Task

class ReasoningEngine:
    def __init__(self):
        self.state_machine = ReasoningStateMachine()
        self.goal_manager = GoalManager()
        self.reasoner = Reasoner()
        self.failure_handler = FailureHandler()

    def process_goal(self, goal_text: str) -> List[Task]:
        self.state_machine.transition_to(ReasoningState.PLANNING)
        goal = self.goal_manager.create_goal(goal_text)
        strategy = StrategySelector.select_strategy(goal_text)
        
        tasks = TaskDecomposer.decompose(goal_text)
        self.state_machine.transition_to(ReasoningState.REASONING)
        return tasks

    def reason(self, goal: str, context: dict | None = None, session_id: str = "") -> dict:
        decision_obj = self.reasoner.think(goal)
        return {
            "decision": decision_obj.reason,
            "action": decision_obj.action,
            "strategy": decision_obj.strategy or "Default",
            "confidence": 0.9,
            "next_actions": [decision_obj.next_task_id] if decision_obj.next_task_id else []
        }

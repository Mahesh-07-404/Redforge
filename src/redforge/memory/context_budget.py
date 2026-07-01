from ..contracts.memory import ContextBudget


class ContextBudgetManager:
    def __init__(self, total_budget: int = 4096):
        self.total_budget = total_budget

    def get_budget(self) -> ContextBudget:
        return ContextBudget(
            system_prompt=int(self.total_budget * 0.20),
            memory_rag=int(self.total_budget * 0.25),
            conversation_history=int(self.total_budget * 0.35),
            current_turn=int(self.total_budget * 0.15),
            reserved_output=int(self.total_budget * 0.05),
        )

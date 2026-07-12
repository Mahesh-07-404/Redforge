from ..planner.plan import Plan
from ..planner.task import Task


class BaseAgent:
    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.description: str = ""
        self.supported_modes: list[str] = []
        self.supported_tools: list[str] = []
        self.supported_targets: list[str] = []
        self.required_capabilities: list[str] = []

    async def execute(self, plan: Plan) -> str:
        # Dry-run simulate task execution plan outputs
        return f"Agent {self.name} completed execution of {plan.goal}"

    def supports(self, task: Task) -> bool:
        if task.tool_hint and task.tool_hint.lower() in [t.lower() for t in self.supported_tools]:
            return True
        return False

    def health(self) -> str:
        return "healthy"

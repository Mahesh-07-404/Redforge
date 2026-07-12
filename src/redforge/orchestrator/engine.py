import time

from ..planner.plan import Plan
from .agent_loader import AgentLoader
from .agent_registry import AgentRegistry
from .contracts import OrchestrationResult
from .coordinator import AgentCoordinator
from .scheduler import AgentScheduler


class OrchestratorEngine:
    def __init__(self):
        self.registry = AgentRegistry()
        AgentLoader.load_agents(self.registry)
        self.coordinator = AgentCoordinator(self.registry)
        self.scheduler = AgentScheduler()

    async def orchestrate(self, plan: Plan) -> OrchestrationResult:
        start_time = time.time()

        assignments = self.coordinator.select_agents_for_plan(plan)
        agent_results = await self.scheduler.schedule_agents(assignments)

        status = "completed"
        for r in agent_results:
            if r.status == "failed":
                status = "failed"
                break

        duration = time.time() - start_time
        return OrchestrationResult(
            plan_goal=plan.goal, status=status, agent_results=agent_results, duration=duration
        )

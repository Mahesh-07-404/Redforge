import time
from typing import List, Optional
from .agent_registry import AgentRegistry
from .agent_loader import AgentLoader
from .coordinator import AgentCoordinator
from .scheduler import AgentScheduler
from .result_merger import ResultMerger
from .contracts import OrchestrationResult
from ..planner.plan import Plan

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
            plan_goal=plan.goal,
            status=status,
            agent_results=agent_results,
            duration=duration
        )

from ..agents.base import BaseAgent
from ..planner.plan import Plan
from .contracts import AgentTaskResult
from .dispatcher import AgentDispatcher


class AgentScheduler:
    def __init__(self):
        self.dispatcher = AgentDispatcher()

    async def schedule_agents(
        self, assignments: list[tuple[BaseAgent, Plan]]
    ) -> list[AgentTaskResult]:
        results = []
        for agent, plan in assignments:
            res = await self.dispatcher.dispatch(agent, plan)
            results.append(res)
        return results

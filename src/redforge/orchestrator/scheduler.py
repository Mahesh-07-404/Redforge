import asyncio
from typing import List
from .contracts import AgentTaskResult
from .dispatcher import AgentDispatcher
from ..agents.base import BaseAgent
from ..planner.plan import Plan

class AgentScheduler:
    def __init__(self):
        self.dispatcher = AgentDispatcher()

    async def schedule_agents(self, assignments: List[tuple[BaseAgent, Plan]]) -> List[AgentTaskResult]:
        results = []
        for agent, plan in assignments:
            res = await self.dispatcher.dispatch(agent, plan)
            results.append(res)
        return results

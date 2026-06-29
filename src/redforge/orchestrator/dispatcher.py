import time
from ..agents.base import BaseAgent
from ..planner.plan import Plan
from .contracts import AgentTaskResult

class AgentDispatcher:
    async def dispatch(self, agent: BaseAgent, plan: Plan) -> AgentTaskResult:
        start_time = time.time()
        output = await agent.execute(plan)
        duration = time.time() - start_time
        
        return AgentTaskResult(
            task_id=plan.goal,
            agent_id=agent.id,
            status="completed" if agent.health() == "healthy" else "failed",
            output=output,
            duration=duration
        )

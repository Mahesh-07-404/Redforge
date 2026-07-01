from ..agents.base import BaseAgent
from ..planner.plan import Plan
from .agent_registry import AgentRegistry


class AgentCoordinator:
    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    def select_agents_for_plan(self, plan: Plan) -> list[tuple[BaseAgent, Plan]]:
        assignments = []
        for task in plan.ordered_tasks:
            assigned = False
            for agent in self.registry.list_agents():
                if agent.supports(task):
                    assignments.append((agent, plan))
                    assigned = True
                    break
            if not assigned:
                recon = self.registry.lookup_agent("recon_agent")
                if recon:
                    assignments.append((recon, plan))
        return assignments

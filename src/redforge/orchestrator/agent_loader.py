from ..agents import (
    AndroidAgent,
    BugBountyAgent,
    CoordinatorAgent,
    CTFAgent,
    LearningAgent,
    NetworkAgent,
    ReconAgent,
    ReportAgent,
    ResearchAgent,
    WebAgent,
)
from .agent_registry import AgentRegistry


class AgentLoader:
    @staticmethod
    def load_agents(registry: AgentRegistry):
        agents_list = [
            ReconAgent(),
            WebAgent(),
            NetworkAgent(),
            AndroidAgent(),
            CTFAgent(),
            LearningAgent(),
            ReportAgent(),
            ResearchAgent(),
            BugBountyAgent(),
            CoordinatorAgent(),
        ]
        for agent in agents_list:
            registry.register_agent(agent)

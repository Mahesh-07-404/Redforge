from ..agents.base import BaseAgent


class AgentRegistry:
    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}

    def register_agent(self, agent: BaseAgent):
        self._agents[agent.id] = agent

    def lookup_agent(self, agent_id: str) -> BaseAgent | None:
        return self._agents.get(agent_id)

    def list_agents(self) -> list[BaseAgent]:
        return list(self._agents.values())

    def get_agents_by_capability(self, capability: str) -> list[BaseAgent]:
        return [a for a in self._agents.values() if capability in a.required_capabilities]

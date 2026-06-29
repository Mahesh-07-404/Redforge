from typing import Dict, List, Optional
from ..agents.base import BaseAgent

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register_agent(self, agent: BaseAgent):
        self._agents[agent.id] = agent

    def lookup_agent(self, agent_id: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[BaseAgent]:
        return list(self._agents.values())

    def get_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        return [a for a in self._agents.values() if capability in a.required_capabilities]

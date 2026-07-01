from .base import BaseAgent


class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.id = "research_agent"
        self.name = "Research Agent"
        self.description = "Performs CVE searches and technology security research"
        self.supported_modes = ["learning"]
        self.supported_tools = ["search"]
        self.required_capabilities = ["RESEARCH"]

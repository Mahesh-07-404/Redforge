from .base import BaseAgent

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.id = "coordinator_agent"
        self.name = "Coordinator Agent"
        self.description = "Coordinates task handoffs and maps high-level goals to agents"
        self.supported_modes = ["pentest", "bugbounty", "ctf", "learning"]
        self.supported_tools = []
        self.required_capabilities = ["COORDINATION"]

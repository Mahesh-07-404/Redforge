from .base import BaseAgent

class ReportAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.id = "report_agent"
        self.name = "Reporting Agent"
        self.description = "Generates penetration testing and bug bounty reports"
        self.supported_modes = ["report"]
        self.supported_tools = []
        self.required_capabilities = ["REPORT_GENERATION"]

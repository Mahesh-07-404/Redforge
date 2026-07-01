from .base import BaseAgent


class BugBountyAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.id = "bugbounty_agent"
        self.name = "Bug Bounty Agent"
        self.description = "Identifies vulnerabilities in bug bounty scopes"
        self.supported_modes = ["bugbounty"]
        self.supported_tools = ["subfinder", "httpx", "nuclei"]
        self.required_capabilities = ["BUG_BOUNTY_ASSESSMENT"]

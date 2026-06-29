from .base import BaseAgent

class ReconAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.id = "recon_agent"
        self.name = "Recon Agent"
        self.description = "Performs initial passive/active domain & subdomain reconnaissance"
        self.supported_modes = ["recon", "bugbounty", "pentest"]
        self.supported_tools = ["subfinder", "amass", "assetfinder", "dnsx"]
        self.required_capabilities = ["SUBDOMAIN_ENUMERATION", "DNS_ENUMERATION"]

from .base import BaseAgent

class NetworkAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.id = "network_agent"
        self.name = "Network Scanning Agent"
        self.description = "Performs port scanning, service version detection, and network analysis"
        self.supported_modes = ["pentest"]
        self.supported_tools = ["nmap", "masscan", "naabu"]
        self.required_capabilities = ["PORT_SCANNING"]

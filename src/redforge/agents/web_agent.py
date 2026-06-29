from .base import BaseAgent

class WebAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.id = "web_agent"
        self.name = "Web Vulnerability Agent"
        self.description = "Identifies vulnerabilities in HTTP, web applications, and web services"
        self.supported_modes = ["pentest", "bugbounty"]
        self.supported_tools = ["httpx", "katana", "nuclei", "ffuf", "feroxbuster", "zap", "burpsuite"]
        self.required_capabilities = ["WEB_CRAWLING", "HTTP_ENUMERATION", "TECHNOLOGY_DETECTION"]

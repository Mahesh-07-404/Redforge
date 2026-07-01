from .capabilities import Capability
from .discovery import ToolDiscovery
from .exceptions import ToolNotFoundError
from .tool import Tool


class ToolRegistry:
    def __init__(self):
        self._cache: dict[str, Tool] = {}
        self._tools = self._initialize_tools()

    def _initialize_tools(self) -> dict[str, Tool]:
        tools_dict = {
            "subfinder": Tool(
                id="subfinder",
                name="subfinder",
                binary="subfinder",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest"],
                categories=["recon"],
                description="Subdomain discovery tool",
                capabilities=[Capability.SUBDOMAIN_ENUMERATION],
                install_method="go",
                package="subfinder",
                install_command="go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
                category="recon",
                essential=True,
            ),
            "httpx": Tool(
                id="httpx",
                name="httpx",
                binary="httpx",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest"],
                categories=["recon"],
                description="Fast and multi-purpose HTTP toolkit",
                capabilities=[Capability.HTTP_ENUMERATION, Capability.TECHNOLOGY_DETECTION],
                install_method="go",
                package="httpx",
                install_command="go install github.com/projectdiscovery/httpx/cmd/httpx@latest",
                category="recon",
            ),
            "katana": Tool(
                id="katana",
                name="katana",
                binary="katana",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest"],
                categories=["recon"],
                description="Next-generation crawling and spidering framework",
                capabilities=[Capability.WEB_CRAWLING],
                install_method="go",
                package="katana",
                install_command="go install github.com/projectdiscovery/katana/cmd/katana@latest",
                category="recon",
            ),
            "nuclei": Tool(
                id="nuclei",
                name="nuclei",
                binary="nuclei",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest", "ctf"],
                categories=["web", "vuln"],
                description="Fast and customizable vulnerability scanner",
                capabilities=[Capability.TECHNOLOGY_DETECTION],
                install_method="go",
                package="nuclei",
                install_command="go install github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest",
                category="web",
                essential=True,
            ),
            "amass": Tool(
                id="amass",
                name="amass",
                binary="amass",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest"],
                categories=["recon"],
                description="In-depth DNS enumeration and network mapping",
                capabilities=[Capability.SUBDOMAIN_ENUMERATION, Capability.DNS_ENUMERATION],
                install_method="go",
                package="amass",
                install_command="go install github.com/OWASP/Amass/v3/...@latest",
                category="recon",
            ),
            "assetfinder": Tool(
                id="assetfinder",
                name="assetfinder",
                binary="assetfinder",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty"],
                categories=["recon"],
                description="Find domains and subdomains related to a target domain",
                capabilities=[Capability.SUBDOMAIN_ENUMERATION],
                install_method="go",
                package="assetfinder",
                install_command="go install github.com/tomnomnom/assetfinder@latest",
                category="recon",
            ),
            "gau": Tool(
                id="gau",
                name="gau",
                binary="gau",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty"],
                categories=["recon"],
                description="GetAllUrls from various public sources",
                capabilities=[Capability.HTTP_ENUMERATION],
                install_method="go",
                package="gau",
                install_command="go install github.com/lc/gau/v2/cmd/gau@latest",
                category="recon",
            ),
            "waybackurls": Tool(
                id="waybackurls",
                name="waybackurls",
                binary="waybackurls",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty"],
                categories=["recon"],
                description="Fetch URLs from the Wayback Machine",
                capabilities=[Capability.HTTP_ENUMERATION],
                install_method="go",
                package="waybackurls",
                install_command="go install github.com/tomnomnom/waybackurls@latest",
                category="recon",
            ),
            "ffuf": Tool(
                id="ffuf",
                name="ffuf",
                binary="ffuf",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest", "ctf"],
                categories=["recon", "fuzzing"],
                description="Fast web fuzzer",
                capabilities=[Capability.DIRECTORY_BRUTE_FORCE, Capability.FUZZING],
                install_method="go",
                package="ffuf",
                install_command="go install github.com/ffuf/ffuf@latest",
                category="recon",
                essential=True,
            ),
            "feroxbuster": Tool(
                id="feroxbuster",
                name="feroxbuster",
                binary="feroxbuster",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest"],
                categories=["recon"],
                description="Fast, simple, recursive content discovery tool",
                capabilities=[Capability.DIRECTORY_BRUTE_FORCE],
                install_method="cargo",
                package="feroxbuster",
                install_command="cargo install feroxbuster",
                category="recon",
            ),
            "nmap": Tool(
                id="nmap",
                name="nmap",
                binary="nmap",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest", "ctf"],
                categories=["recon", "scanning"],
                description="Network exploration tool and port scanner",
                capabilities=[Capability.PORT_SCANNING],
                install_method="apt",
                package="nmap",
                install_command="sudo apt install -y nmap",
                category="recon",
                essential=True,
            ),
            "sqlmap": Tool(
                id="sqlmap",
                name="sqlmap",
                binary="sqlmap",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest", "ctf"],
                categories=["exploitation"],
                description="Automatic SQL injection and database takeover tool",
                capabilities=[Capability.FUZZING],
                install_method="apt",
                package="sqlmap",
                install_command="sudo apt install -y sqlmap",
                category="web",
                essential=True,
            ),
            "nikto": Tool(
                id="nikto",
                name="nikto",
                binary="nikto",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["pentest"],
                categories=["web"],
                description="Web server scanner",
                capabilities=[Capability.TECHNOLOGY_DETECTION],
                install_method="apt",
                package="nikto",
                install_command="sudo apt install -y nikto",
                category="web",
            ),
            "dirsearch": Tool(
                id="dirsearch",
                name="dirsearch",
                binary="dirsearch",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest"],
                categories=["recon"],
                description="Web path scanner",
                capabilities=[Capability.DIRECTORY_BRUTE_FORCE],
                install_method="pip",
                package="dirsearch",
                install_command="pip install dirsearch",
                category="recon",
            ),
            "gobuster": Tool(
                id="gobuster",
                name="gobuster",
                binary="gobuster",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest"],
                categories=["recon"],
                description="Directory/File, DNS and VHost busting tool",
                capabilities=[Capability.DIRECTORY_BRUTE_FORCE, Capability.DNS_ENUMERATION],
                install_method="go",
                package="gobuster",
                install_command="go install github.com/OJ/gobuster/v3@latest",
                category="recon",
            ),
            "dnsx": Tool(
                id="dnsx",
                name="dnsx",
                binary="dnsx",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest"],
                categories=["recon"],
                description="Fast and multi-purpose DNS toolkit",
                capabilities=[Capability.DNS_ENUMERATION],
                install_method="go",
                package="dnsx",
                install_command="go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest",
                category="recon",
            ),
            "naabu": Tool(
                id="naabu",
                name="naabu",
                binary="naabu",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest"],
                categories=["recon"],
                description="Fast port scanner written in Go",
                capabilities=[Capability.PORT_SCANNING],
                install_method="go",
                package="naabu",
                install_command="go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest",
                category="recon",
            ),
            "masscan": Tool(
                id="masscan",
                name="masscan",
                binary="masscan",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows WSL",
                ],
                supported_modes=["pentest"],
                categories=["recon"],
                description="TCP port scanner, spews packets asynchronously",
                capabilities=[Capability.PORT_SCANNING],
                install_method="apt",
                package="masscan",
                install_command="sudo apt install -y masscan",
                category="recon",
            ),
            "burpsuite": Tool(
                id="burpsuite",
                name="burpsuite",
                binary="burpsuite",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest"],
                categories=["web"],
                description="Integrated platform for security testing of web applications",
                capabilities=[Capability.FUZZING, Capability.WEB_CRAWLING],
                install_method="apt",
                package="burpsuite",
                install_command="sudo apt install -y burpsuite",
                category="web",
                essential=True,
            ),
            "zap": Tool(
                id="zap",
                name="zap",
                binary="zaproxy",
                platforms=[
                    "Arch Linux",
                    "Kali Linux",
                    "Ubuntu",
                    "Debian",
                    "Fedora",
                    "macOS",
                    "Windows",
                    "Windows WSL",
                ],
                supported_modes=["bugbounty", "pentest"],
                categories=["web"],
                description="OWASP Zed Attack Proxy",
                capabilities=[Capability.FUZZING, Capability.WEB_CRAWLING],
                install_method="apt",
                package="zaproxy",
                install_command="sudo apt install -y zaproxy",
                category="web",
            ),
        }
        return tools_dict

    def register_tool(self, tool: Tool):
        self._tools[tool.id] = tool
        if tool.id in self._cache:
            del self._cache[tool.id]

    def lookup_tool_by_name(self, name: str) -> Tool:
        if name in self._cache:
            return self._cache[name]
        for t_id, tool in self._tools.items():
            if (
                tool.name.lower() == name.lower()
                or tool.id.lower() == name.lower()
                or tool.binary.lower() == name.lower()
            ):
                binary_path = ToolDiscovery.find_binary(tool.binary)
                if binary_path:
                    tool.availability = True
                    tool.health = "healthy"
                else:
                    tool.availability = False
                    tool.health = "unknown"
                self._cache[name] = tool
                return tool
        raise ToolNotFoundError(f"Tool '{name}' not found in registry.")

    def lookup_tools_by_capability(self, capability: str) -> list[Tool]:
        results = []
        for tool in self._tools.values():
            if capability in tool.capabilities:
                binary_path = ToolDiscovery.find_binary(tool.binary)
                if binary_path:
                    tool.availability = True
                    tool.health = "healthy"
                else:
                    tool.availability = False
                    tool.health = "unknown"
                results.append(tool)

        ranking_order = {
            "subfinder": 1,
            "amass": 2,
            "assetfinder": 3,
            "httpx": 1,
            "gau": 2,
            "waybackurls": 3,
            "nmap": 1,
            "masscan": 2,
            "naabu": 3,
            "ffuf": 1,
            "feroxbuster": 2,
            "dirsearch": 3,
            "gobuster": 4,
            "katana": 1,
            "dnsx": 1,
            "zap": 1,
            "burpsuite": 2,
        }
        results.sort(key=lambda t: ranking_order.get(t.id, 99))
        return results

    def get_tool_metadata(self, tool_id: str) -> Tool | None:
        try:
            return self.lookup_tool_by_name(tool_id)
        except ToolNotFoundError:
            return None

    def list_available(self) -> list[str]:
        return ["nmap", "ffuf", "sqlmap"]

    @classmethod
    def get_tool(cls, name: str) -> Tool | None:
        registry = cls()
        try:
            return registry.lookup_tool_by_name(name)
        except ToolNotFoundError:
            return None

    @classmethod
    def get_all_tools(cls) -> dict[str, Tool]:
        registry = cls()
        return registry._tools

    @classmethod
    def get_tools_by_category(cls, category: str) -> list[Tool]:
        registry = cls()
        return [
            t
            for t in registry._tools.values()
            if category in t.categories or t.category == category
        ]

    @classmethod
    def get_essential_tools(cls) -> list[Tool]:
        registry = cls()
        return [t for t in registry._tools.values() if t.essential]


ToolRegistry.TOOLS = ToolRegistry()._tools

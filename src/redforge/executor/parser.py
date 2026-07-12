import re
from typing import Any


class OutputParser:
    @staticmethod
    def parse(tool_name: str, raw_output: str) -> dict[str, Any]:
        tool_lower = tool_name.lower().strip()
        structured: dict[str, Any] = {}

        if not raw_output:
            return structured

        if "subfinder" in tool_lower:
            subdomains = []
            for line in raw_output.splitlines():
                line_str = line.strip()
                if line_str and not line_str.startswith("["):
                    subdomains.append(line_str)
            structured["subdomains"] = subdomains

        elif "nmap" in tool_lower:
            ports = []
            for line in raw_output.splitlines():
                match = re.search(r"(\d+)/(tcp|udp)\s+(\w+)\s+(.*)", line)
                if match:
                    ports.append(
                        {
                            "port": int(match.group(1)),
                            "protocol": match.group(2),
                            "state": match.group(3),
                            "service": match.group(4).strip(),
                        }
                    )
            structured["ports"] = ports

        elif "httpx" in tool_lower:
            urls = []
            for line in raw_output.splitlines():
                line_str = line.strip()
                if line_str.startswith("http://") or line_str.startswith("https://"):
                    urls.append(line_str)
            structured["urls"] = urls

        return structured

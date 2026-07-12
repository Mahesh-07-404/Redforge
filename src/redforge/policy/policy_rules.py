class PolicyRules:
    PROHIBITED_TARGETS = ["localhost", "127.0.0.1", "0.0.0.0", "::1"]

    TOOL_RISK_MAP = {
        "nmap": "MEDIUM",
        "masscan": "HIGH",
        "naabu": "MEDIUM",
        "subfinder": "LOW",
        "amass": "MEDIUM",
        "assetfinder": "LOW",
        "httpx": "LOW",
        "katana": "MEDIUM",
        "nuclei": "HIGH",
        "ffuf": "MEDIUM",
        "feroxbuster": "MEDIUM",
        "dirsearch": "MEDIUM",
        "gobuster": "MEDIUM",
        "sqlmap": "CRITICAL",
        "nikto": "MEDIUM",
        "zap": "HIGH",
        "burpsuite": "HIGH",
        "dnsx": "LOW",
        "gau": "LOW",
        "waybackurls": "LOW",
    }

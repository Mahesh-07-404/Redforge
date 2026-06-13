"""RedForge Dynamic Skill Loader"""

from typing import List, Optional, Dict, Any
from redforge.skills.registry import SkillRegistry, SkillMetadata

class DynamicSkillLoader:
    """Dynamically loads and selects skills based on intent, limiting context size"""

    def __init__(self, registry: SkillRegistry):
        self.registry = registry

    def select_skills(self, intent: str, active_mode: str, query: str) -> List[SkillMetadata]:
        """
        Select skills dynamically according to the V2 rules.
        Maximum loaded: 5, hard limit: 10.
        """
        selected: List[SkillMetadata] = []

        # Ensure registry is loaded
        if not self.registry.skills:
            self.registry.load_registry()

        all_skills = self.registry.list_skills()

        # Helper to find skills by name/category
        def find_by_name(name_sub: str, category: str) -> Optional[SkillMetadata]:
            for s in all_skills:
                if s.category == category.upper() and name_sub.lower() in s.name.lower():
                    return s
            return None

        # 1. Tier 0 System skills based on intent
        # For CHAT / any intent, personality and conversation are essential core
        personality = find_by_name("personality", "SYSTEM")
        conversation = find_by_name("conversation", "SYSTEM")
        anti_hallucination = find_by_name("anti_hallucination", "SYSTEM")
        
        if personality:
            selected.append(personality)
        if conversation:
            selected.append(conversation)
        if anti_hallucination:
            selected.append(anti_hallucination)

        # 2. Tier 1 Safety skills
        if intent in ("RECON", "SCAN", "REPORT"):
            scope_skill = find_by_name("scope_and_authorization", "SAFETY")
            legal_skill = find_by_name("legal_and_compliance", "SAFETY")
            if scope_skill:
                selected.append(scope_skill)
            if legal_skill:
                selected.append(legal_skill)

        # 3. Tier 2 Mode skills based on active mode
        if active_mode:
            mode_skill = find_by_name(active_mode.lower(), "MODES")
            if mode_skill:
                selected.append(mode_skill)

        # 4. Tier 3 Tool skills matching query keywords
        if intent in ("RECON", "SCAN"):
            query_lower = query.lower()
            tool_keywords = {
                "01_recon_tools": ["recon", "whois", "dns", "subdomain", "enum", "dig", "cert", "subfinder", "dns_enum"],
                "02_web_tools": ["web", "http", "url", "ffuf", "curl", "whatweb", "http_get", "dirb", "gobuster", "dir"],
                "03_binary_tools": ["binary", "elf", "gdb", "ropper", "checksec", "pwntools", "exploit", "assembly", "compile", "pwn"],
                "04_forensics_tools": ["forensic", "binwalk", "exiftool", "strings", "file", "analysis", "wireshark", "pcap"],
                "05_password_tools": ["password", "hydra", "john", "hashcat", "crack", "brute", "wordlist"],
                "06_network_tools": ["network", "nmap", "port", "ip", "host", "ping", "scan"],
                "07_exploitation_tools": ["exploit", "payload", "shell", "reverse", "metasploit", "msf", "reverse_shell"],
                "08_vulnerability_scanners": ["scanner", "nuclei", "nikto", "vuln", "vulnerability"],
                "09_container_cloud": ["container", "docker", "kubernetes", "k8s", "cloud", "aws", "azure", "gcp"],
                "10_wireless_tools": ["wireless", "wifi", "aircrack", "reaver", "wpa", "wep"]
            }
            matched_tools = []
            for s in all_skills:
                if s.category == "TOOLS":
                    matched = False
                    for filename, kw_list in tool_keywords.items():
                        if filename in s.name:
                            if any(kw in query_lower for kw in kw_list):
                                matched = True
                                break
                    if matched:
                        matched_tools.append(s)

            # Fallback default tools for SCAN/RECON
            if not matched_tools:
                for s in all_skills:
                    if s.category == "TOOLS":
                        if any(x in s.name for x in ("01_recon_tools", "06_network_tools", "08_vulnerability_scanners")):
                            matched_tools.append(s)
            
            selected.extend(matched_tools)

        # 5. Tier 4 Execution skills
        if intent not in ("CHAT", "LEARNING", "CODING"):
            exec_workflow = find_by_name("execution_workflow", "EXECUTION")
            reporting_standards = find_by_name("reporting_standards", "EXECUTION")
            if exec_workflow:
                selected.append(exec_workflow)
            if reporting_standards:
                selected.append(reporting_standards)

        # Deduplicate while preserving order
        unique_selected = []
        seen = set()
        for s in selected:
            if s.name not in seen:
                seen.add(s.name)
                unique_selected.append(s)

        # Enforce limits: target 5, hard limit 10
        if len(unique_selected) > 10:
            unique_selected = unique_selected[:10]

        return unique_selected

    def build_context(self, selected_skills: List[SkillMetadata]) -> str:
        """Format selected skills into a clean system context block"""
        parts = []
        for s in selected_skills:
            parts.append(f"### [{s.category}] {s.name}\n{s.content}")
        return "\n\n".join(parts)

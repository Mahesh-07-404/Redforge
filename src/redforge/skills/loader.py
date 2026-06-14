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

        # 1. Tier 0 System skills (Select up to 3 relevant system skills)
        t0_all = [s for s in all_skills if s.category == "SYSTEM"]
        t0_all.sort(key=lambda s: s.name)
        t0_selected = []
        sys_kws = ["personality", "persona", "conversation", "prompt", "anti_hallucination", "hallucination"]
        for kw in sys_kws:
            for s in t0_all:
                if kw in s.name.lower() and s not in t0_selected:
                    t0_selected.append(s)
        if not t0_selected:
            t0_selected = t0_all[:3]
        selected.extend(t0_selected[:3])

        # 2. Tier 1 Safety skills (Select up to 2 relevant safety skills)
        t1_all = [s for s in all_skills if s.category == "SAFETY"]
        t1_all.sort(key=lambda s: s.name)
        t1_selected = []
        safe_kws = ["scope", "authorization", "legal", "compliance", "privacy"]
        for kw in safe_kws:
            for s in t1_all:
                if kw in s.name.lower() and s not in t1_selected:
                    t1_selected.append(s)
        if not t1_selected:
            t1_selected = t1_all[:2]
        selected.extend(t1_selected[:2])

        # 3. Tier 2 Mode skills based on active mode
        if active_mode:
            norm_mode = active_mode.upper()
            t2_excl = {"02_planning", "03_execution", "04_verification", "16_reporting", "execution_workflow", "reporting_standards"}
            t2_skills = [
                s for s in all_skills 
                if s.category == "MODES" and s.mode == norm_mode
                and not any(excl in s.name for excl in t2_excl)
            ]
            t2_skills.sort(key=lambda s: s.name)
            selected.extend(t2_skills)

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
            
            matched_tools.sort(key=lambda s: s.name)
            selected.extend(matched_tools)

        # 5. Tier 4 Execution skills
        if intent not in ("CHAT", "LEARNING", "CODING"):
            t4_order = ["02_planning", "03_execution", "04_verification", "16_reporting", "execution_workflow", "reporting_standards"]
            t4_skills = []
            for item in t4_order:
                for s in all_skills:
                    if s.category in ("EXECUTION", "AUTONOMY"):
                        if item in s.name:
                            t4_skills.append(s)
                    elif s.category == "MODES" and item in s.name:
                        t4_skills.append(s)
            
            # Deduplicate t4 list
            unique_t4 = []
            seen_t4 = set()
            for s in t4_skills:
                if s.name not in seen_t4:
                    seen_t4.add(s.name)
                    unique_t4.append(s)
            selected.extend(unique_t4)

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

    def build_context(self, selected_skills: List[SkillMetadata], active_mode: str = "bugbounty", intent: str = "SCAN") -> str:
        """Format selected skills into a clean system context block grouped by Tiers"""
        parts = []

        # Tier 0 - CORE SYSTEM
        parts.append("=== TIER 0: CORE SYSTEM ===")
        t0 = [s for s in selected_skills if s.category == "SYSTEM"]
        for s in t0:
            parts.append(f"### [CORE] {s.name}\n{s.content}")

        # Tier 1 - SAFETY
        parts.append("\n=== TIER 1: SAFETY ===")
        t1 = [s for s in selected_skills if s.category == "SAFETY"]
        for s in t1:
            parts.append(f"### [SAFETY] {s.name}\n{s.content}")

        # Tier 2 - ACTIVE MODE
        parts.append(f"\n=== TIER 2: ACTIVE MODE ({active_mode.upper()}) ===")
        t2_excl = {"02_planning", "03_execution", "04_verification", "16_reporting", "execution_workflow", "reporting_standards"}
        t2 = [s for s in selected_skills if s.category == "MODES" and not any(x in s.name for x in t2_excl)]
        for s in t2:
            parts.append(f"### [MODE] {s.name}\n{s.content}")

        # Tier 3 - TOOLS
        parts.append("\n=== TIER 3: REQUIRED TOOLS ===")
        t3 = [s for s in selected_skills if s.category == "TOOLS"]
        for s in t3:
            parts.append(f"### [TOOL] {s.name}\n{s.content}")

        # Tier 4 - EXECUTION
        if intent not in ("CHAT", "LEARNING", "CODING"):
            parts.append("\n=== TIER 4: EXECUTION ===")
            t4 = [s for s in selected_skills if s.category in ("EXECUTION", "AUTONOMY") or any(x in s.name for x in t2_excl)]
            
            # Sort according to standard order
            t4_order = ["02_planning", "03_execution", "04_verification", "16_reporting", "execution_workflow", "reporting_standards"]
            ordered_t4 = []
            for item in t4_order:
                for s in t4:
                    if item in s.name and s not in ordered_t4:
                        ordered_t4.append(s)
            
            # Append anything that didn't match standard order at the end
            for s in t4:
                if s not in ordered_t4:
                    ordered_t4.append(s)
                    
            for s in ordered_t4:
                parts.append(f"### [EXECUTION] {s.name}\n{s.content}")

        return "\n\n".join(parts)

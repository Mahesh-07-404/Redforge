"""RedForge Dynamic Skill Loader"""

import logging

from redforge.skills.registry import SkillMetadata, SkillRegistry

logger = logging.getLogger(__name__)


class DynamicSkillLoader:
    """Dynamically loads and selects skills based on intent, limiting context size"""

    def __init__(self, registry: SkillRegistry):
        self.registry = registry

    def select_skills(self, intent: str, active_mode: str, query: str) -> list[SkillMetadata]:
        """
        Select skills dynamically using RAG (semantic search) and keyword relevance.
        Maximum loaded: 5, hard limit: 10.
        """
        selected: list[SkillMetadata] = []

        # Ensure registry is loaded
        if not self.registry.skills:
            self.registry.load_registry()

        all_skills = self.registry.list_skills()

        # 1. Tier 0 System skills (Select up to 3 relevant system skills)
        t0_all = [s for s in all_skills if s.category == "SYSTEM"]
        t0_all.sort(key=lambda s: s.name)
        t0_selected = []
        sys_kws = [
            "personality",
            "persona",
            "conversation",
            "prompt",
            "anti_hallucination",
            "hallucination",
        ]
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

        # 3. Tier 2 Mode / Capability skills (Dynamic Selection via RAG & relevance)
        rag_skills = []

        # Backward compatibility: if active_mode is a legacy mode, load matching MODES skills.
        if active_mode and active_mode.upper() != "AUTONOMOUS":
            norm_mode = active_mode.upper()
            t2_excl = {
                "02_planning",
                "03_execution",
                "04_verification",
                "16_reporting",
                "execution_workflow",
                "reporting_standards",
            }
            for s in all_skills:
                if (
                    s.category == "MODES"
                    and s.mode == norm_mode
                    and not any(excl in s.name for excl in t2_excl)
                ):
                    rag_skills.append(s)

        if query:
            # A. Try RAG/semantic search via indexer first
            if hasattr(self.registry, "_indexer") and self.registry._indexer:
                try:
                    results = self.registry._indexer.search_skills(query, limit=5)
                    for r in results:
                        name = r.metadata.get("name")
                        if name:
                            for s in all_skills:
                                if s.name.lower() == name.lower() or s.path.endswith(name):
                                    if s.category not in (
                                        "SYSTEM",
                                        "SAFETY",
                                        "TOOLS",
                                        "EXECUTION",
                                        "AUTONOMY",
                                    ):
                                        rag_skills.append(s)
                                        break
                except Exception as e:
                    logger.debug("RAG search failed: %s", e)

            # B. Complement with keyword relevance search
            query_tokens = set(query.lower().split())
            scored_skills = []
            for s in all_skills:
                if s.category in ("SYSTEM", "SAFETY", "TOOLS", "EXECUTION", "AUTONOMY"):
                    continue
                blob = (
                    s.name
                    + " "
                    + s.content
                    + " "
                    + s.category
                    + " "
                    + " ".join(str(t) for t in s.tags)
                ).lower()
                score = sum(1.0 for tok in query_tokens if tok in blob)
                if s.name.lower() in query.lower():
                    score += 2.0
                if score > 0:
                    scored_skills.append((score, s))

            scored_skills.sort(key=lambda x: x[0], reverse=True)
            for _, s in scored_skills[:5]:
                if s not in rag_skills:
                    rag_skills.append(s)

        # Append RAG / capability skills
        selected.extend(rag_skills[:5])

        # 4. Tier 3 Tool skills matching query keywords
        if intent in ("RECON", "SCAN") and query:
            query_lower = query.lower()
            tool_keywords = {
                "01_recon_tools": [
                    "recon",
                    "whois",
                    "dns",
                    "subdomain",
                    "enum",
                    "dig",
                    "cert",
                    "subfinder",
                ],
                "02_web_tools": ["web", "http", "url", "ffuf", "curl", "dirb", "gobuster"],
                "03_binary_tools": ["binary", "elf", "gdb", "ropper", "pwntools", "pwn"],
                "04_forensics_tools": [
                    "forensic",
                    "binwalk",
                    "exiftool",
                    "strings",
                    "wireshark",
                    "pcap",
                ],
                "05_password_tools": ["password", "hydra", "john", "hashcat", "crack", "brute"],
                "06_network_tools": ["network", "nmap", "port", "ip", "host", "ping", "scan"],
                "07_exploitation_tools": ["exploit", "payload", "shell", "metasploit", "msf"],
                "08_vulnerability_scanners": [
                    "scanner",
                    "nuclei",
                    "nikto",
                    "vuln",
                    "vulnerability",
                ],
                "09_container_cloud": [
                    "container",
                    "docker",
                    "kubernetes",
                    "k8s",
                    "cloud",
                    "aws",
                    "azure",
                    "gcp",
                ],
                "10_wireless_tools": ["wireless", "wifi", "aircrack", "reaver"],
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

            if not matched_tools:
                for s in all_skills:
                    if s.category == "TOOLS":
                        if any(
                            x in s.name
                            for x in (
                                "01_recon_tools",
                                "06_network_tools",
                                "08_vulnerability_scanners",
                            )
                        ):
                            matched_tools.append(s)

            matched_tools.sort(key=lambda s: s.name)
            selected.extend(matched_tools)

        # 5. Tier 4 Execution / Autonomy skills
        if intent not in ("CHAT", "LEARNING", "CODING"):
            t4_order = [
                "02_planning",
                "03_execution",
                "04_verification",
                "16_reporting",
                "execution_workflow",
                "reporting_standards",
            ]
            t4_skills = []
            for item in t4_order:
                for s in all_skills:
                    if s.category in ("EXECUTION", "AUTONOMY"):
                        if item in s.name:
                            t4_skills.append(s)
                    elif s.category == "MODES" and item in s.name:
                        t4_skills.append(s)

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

        # Enforce limits (target 5, hard limit 10)
        if len(unique_selected) > 10:
            unique_selected = unique_selected[:10]

        return unique_selected

    def build_context(
        self,
        selected_skills: list[SkillMetadata],
        active_mode: str = "autonomous",
        intent: str = "SCAN",
    ) -> str:
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

        # Tier 2 - ACTIVE CAPABILITIES / METHODOLOGY
        parts.append(f"\n=== TIER 2: ACTIVE MODE ({active_mode.upper()}) ===")
        t2_excl = {
            "02_planning",
            "03_execution",
            "04_verification",
            "16_reporting",
            "execution_workflow",
            "reporting_standards",
        }
        t2 = [
            s
            for s in selected_skills
            if s.category not in ("SYSTEM", "SAFETY", "TOOLS", "EXECUTION", "AUTONOMY")
            and not any(x in s.name for x in t2_excl)
        ]
        for s in t2:
            parts.append(f"### [CAPABILITY] {s.name}\n{s.content}")

        # Tier 3 - TOOLS
        parts.append("\n=== TIER 3: REQUIRED TOOLS ===")
        t3 = [s for s in selected_skills if s.category == "TOOLS"]
        for s in t3:
            parts.append(f"### [TOOL] {s.name}\n{s.content}")

        # Tier 4 - EXECUTION
        if intent not in ("CHAT", "LEARNING", "CODING"):
            parts.append("\n=== TIER 4: EXECUTION ===")
            t4 = [
                s
                for s in selected_skills
                if s.category in ("EXECUTION", "AUTONOMY") or any(x in s.name for x in t2_excl)
            ]

            t4_order = [
                "02_planning",
                "03_execution",
                "04_verification",
                "16_reporting",
                "execution_workflow",
                "reporting_standards",
            ]
            ordered_t4 = []
            for item in t4_order:
                for s in t4:
                    if item in s.name and s not in ordered_t4:
                        ordered_t4.append(s)

            for s in t4:
                if s not in ordered_t4:
                    ordered_t4.append(s)

            for s in ordered_t4:
                parts.append(f"### [EXECUTION] {s.name}\n{s.content}")

        return "\n\n".join(parts)


SkillService = DynamicSkillLoader

"""Skill loader for agent instructions and knowledge"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Skill:
    name: str
    path: str
    content: str
    category: str
    mode: Optional[str] = None
    difficulty: str = "intermediate"
    tags: List[str] = field(default_factory=list)
    loaded_at: Optional[datetime] = None


class SkillLoader:
    """Loads and manages skill files for the agent"""

    # src/redforge/core/skill_loader.py  →  go up 4 levels to reach project root, then skills/
    _DEFAULT_SKILLS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "skills"

    def __init__(self, skills_dir: Optional[str] = None):
        if skills_dir:
            self.skills_dir = Path(skills_dir)
        else:
            self.skills_dir = self._DEFAULT_SKILLS_DIR

        self._skills: Dict[str, "Skill"] = {}
        self._mode_skills: Dict[str, List[str]] = {}
        self._loaded = False

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_skills(self) -> None:
        """Load all skill files from the skills directory"""
        if not self.skills_dir.exists():
            self._create_default_skills()
            return

        self._skills = {}
        self._mode_skills = {}

        for root, dirs, files in os.walk(self.skills_dir):
            dirs[:] = [d for d in dirs if not d.startswith(("__", ".", "cache", "versions", "adaptive"))]
            root_path = Path(root)

            for fname in files:
                if fname.endswith(".md") or fname.endswith(".json"):
                    file_path = root_path / fname
                    try:
                        skill = self._load_skill_file(file_path)
                        if skill:
                            self._skills[skill.name] = skill
                            for key in _index_keys(skill):
                                self._mode_skills.setdefault(key, []).append(skill.name)
                    except Exception as exc:
                        pass  # silently skip unreadable files

        self._loaded = True

    def _load_skill_file(self, file_path: Path) -> Optional["Skill"]:
        """Load a single skill file"""
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()

        if not content.strip():
            return None

        try:
            relative = file_path.relative_to(self.skills_dir)
        except ValueError:
            relative = Path(file_path.name)

        parts = relative.parts
        category = parts[0].upper() if len(parts) > 1 else "GENERAL"
        mode = parts[1].upper() if len(parts) > 2 else None
        
        # New V4 logic for MODES: if category is MODES and no subfolder is present (len(parts) == 2),
        # then set mode to the uppercase stem of the filename (e.g. "bugbounty.md" -> mode = "BUGBOUNTY")
        if category == "MODES" and not mode and len(parts) == 2:
            mode = file_path.stem.upper()

        unique_name = "/".join(list(parts[:-1]) + [file_path.stem]) if len(parts) > 1 else file_path.stem

        return Skill(
            name=unique_name,
            path=str(file_path),
            content=content,
            category=category,
            mode=mode,
            loaded_at=datetime.now(),
        )

    def _create_default_skills(self) -> None:
        """Minimal built-in skills when skills directory is missing"""
        defaults = {
            "SYSTEM/persona": (
                "SYSTEM",
                """## RedForge Agent\nAutonomous pentesting AI. Always verify scope. Document findings. Non-destructive first.\n"""
            ),
            "MODES/bugbounty": (
                "MODES",
                """## Bug Bounty Recon\npassive: whois, dns, certs\nactive: nmap, ffuf, subfinder\nvulns: sqli, xss, ssrf, idor\n"""
            ),
            "MODES/ctf": (
                "MODES",
                """## CTF Approach\nWeb: sqli, xss, lfi, idor\nBinary: gdb, pwntools, ropper\nCrypto: padding oracle, xor, rsa\nForensics: binwalk, strings, exiftool\n"""
            ),
        }
        for name, (cat, content) in defaults.items():
            mode = "BUGBOUNTY" if "bugbounty" in name else ("CTF" if "ctf" in name else None)
            self._skills[name] = Skill(
                name=name, path="default", content=content, category=cat, mode=mode, loaded_at=datetime.now()
            )
        self._loaded = True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_context_for_mode(self, mode: str) -> str:
        """Get all loaded skill text relevant to a mode"""
        mode_key = _normalise_mode(mode)
        parts = []

        for skill in self._skills.values():
            if (
                mode_key in skill.name.lower()
                or mode_key in skill.category.lower()
                or (skill.mode and mode_key in skill.mode.lower())
            ):
                parts.append(f"\n\n### [{skill.category}] {skill.name}\n{skill.content}")

        if not parts:
            for skill in self._skills.values():
                if skill.category.upper() == "SYSTEM":
                    parts.append(f"\n\n### {skill.name}\n{skill.content}")

        return "\n".join(parts) if parts else "No skill context available."

    def get_top_k(self, query: str, k: int = 5) -> str:
        """Return top-k skills most relevant to a query (keyword-scored)"""
        query_tokens = set(query.lower().split())
        scored: List[tuple] = []

        for skill in self._skills.values():
            blob = (skill.name + " " + skill.content + " " + skill.category).lower()
            score = sum(1.0 for tok in query_tokens if tok in blob)
            if skill.category.upper() in ("SYSTEM", "TOOLS"):
                score += 0.3
            if score > 0:
                scored.append((score, skill))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for _, skill in scored[:k]:
            snippet = skill.content[:700] + ("\n[...truncated]" if len(skill.content) > 700 else "")
            results.append(f"### [{skill.category}] {skill.name}\n{snippet}")

        return "\n\n".join(results)

    def get_hierarchical_context(
        self,
        active_mode: str,
        intent: str,
        query: str,
    ) -> str:
        """
        Compile and load skills according to the RedForge Tiered Hierarchy.
        Strict Order: Tier 0 -> Tier 1 -> Tier 2 -> Tier 3 -> Tier 4.
        """
        if not self._loaded:
            self.load_skills()

        parts = []

        # TIER 0 - CORE SYSTEM
        parts.append("=== TIER 0: CORE SYSTEM ===")
        tier0_skills = [s for s in self._skills.values() if s.category.upper() == "SYSTEM"]
        tier0_skills.sort(key=lambda s: s.name)
        for s in tier0_skills:
            parts.append(f"### [CORE] {s.name}\n{s.content}")

        # TIER 1 - SAFETY
        parts.append("\n=== TIER 1: SAFETY ===")
        tier1_skills = [s for s in self._skills.values() if s.category.upper() == "SAFETY"]
        tier1_skills.sort(key=lambda s: s.name)
        for s in tier1_skills:
            parts.append(f"### [SAFETY] {s.name}\n{s.content}")

        # TIER 2 - ACTIVE MODE
        parts.append(f"\n=== TIER 2: ACTIVE MODE ({active_mode.upper()}) ===")
        norm_mode = _normalise_mode(active_mode).upper()
        tier4_excl = {"02_planning", "03_execution", "04_verification", "16_reporting"}
        tier2_skills = [
            s for s in self._skills.values() 
            if s.category.upper() == "MODES" and s.mode == norm_mode
            and not any(excl in s.name for excl in tier4_excl)
        ]
        tier2_skills.sort(key=lambda s: s.name)
        for s in tier2_skills:
            parts.append(f"### [MODE] {s.name}\n{s.content}")

        # TIER 3 - TOOL SKILLS
        parts.append("\n=== TIER 3: REQUIRED TOOLS ===")
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
        required_tools = []
        for s in self._skills.values():
            if s.category.upper() == "TOOLS":
                matched = False
                for filename, kw_list in tool_keywords.items():
                    if filename in s.name:
                        if any(kw in query_lower for kw in kw_list):
                            matched = True
                            break
                if matched:
                    required_tools.append(s)

        if not required_tools and intent in ("SCAN", "RECON"):
            # Load recon_tools, network_tools, and vulnerability_scanners as defaults
            for s in self._skills.values():
                if s.category.upper() == "TOOLS":
                    if any(x in s.name for x in ("01_recon_tools", "06_network_tools", "08_vulnerability_scanners")):
                        required_tools.append(s)

        required_tools.sort(key=lambda s: s.name)
        for s in required_tools:
            parts.append(f"### [TOOL] {s.name}\n{s.content}")

        # TIER 4 - EXECUTION (Only when action requested)
        action_requested = intent not in ("CHAT", "LEARNING", "CODING")
        if action_requested:
            parts.append("\n=== TIER 4: EXECUTION ===")
            
            # Load modern V4 EXECUTION category skills
            v4_exec_skills = [s for s in self._skills.values() if s.category.upper() == "EXECUTION"]
            v4_exec_skills.sort(key=lambda s: s.name)
            for s in v4_exec_skills:
                parts.append(f"### [EXECUTION] {s.name}\n{s.content}")

            # Legacy compatibility for tests & old names
            tier4_order = ["02_planning", "03_execution", "04_verification", "16_reporting"]
            tier4_skills = {}
            for s in self._skills.values():
                for item in tier4_order:
                    if item in s.name:
                        tier4_skills[item] = s
            
            for item in tier4_order:
                if item in tier4_skills:
                    s = tier4_skills[item]
                    parts.append(f"### [EXECUTION] {s.name}\n{s.content}")

        return "\n\n".join(parts)

    def get_skill(self, name: str) -> Optional["Skill"]:
        return self._skills.get(name)

    def list_skills(self, category: Optional[str] = None) -> List["Skill"]:
        if category:
            return [s for s in self._skills.values() if s.category.upper() == category.upper()]
        return list(self._skills.values())

    def search_skills(self, query: str) -> List["Skill"]:
        q = query.lower()
        return [s for s in self._skills.values() if q in s.name.lower() or q in s.content.lower()]

    def is_loaded(self) -> bool:
        return self._loaded

    def reload(self) -> None:
        self._loaded = False
        self.load_skills()

    def stats(self) -> Dict[str, Any]:
        by_cat: Dict[str, int] = {}
        for s in self._skills.values():
            by_cat[s.category] = by_cat.get(s.category, 0) + 1
        return {
            "skills_dir": str(self.skills_dir),
            "dir_exists": self.skills_dir.exists(),
            "total": len(self._skills),
            "by_category": by_cat,
        }


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _normalise_mode(mode: str) -> str:
    return {
        "bug": "bugbounty", "bugbounty": "bugbounty",
        "ctf": "ctf", "learning": "learning",
        "coding": "coding", "android": "android",
        "goal": "", "knowledge": "",
    }.get(mode.lower(), mode.lower())


def _index_keys(skill: "Skill") -> List[str]:
    keys = [skill.category.lower()]
    if skill.mode:
        keys.append(skill.mode.lower())
    return keys

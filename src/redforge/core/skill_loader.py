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
            "core/persona": (
                "SYSTEM",
                """## RedForge Agent\nAutonomous pentesting AI. Always verify scope. Document findings. Non-destructive first.\n"""
            ),
            "core/bugbounty": (
                "BUGBOUNTY",
                """## Bug Bounty Recon\npassive: whois, dns, certs\nactive: nmap, ffuf, subfinder\nvulns: sqli, xss, ssrf, idor\n"""
            ),
            "core/ctf": (
                "CTF",
                """## CTF Approach\nWeb: sqli, xss, lfi, idor\nBinary: gdb, pwntools, ropper\nCrypto: padding oracle, xor, rsa\nForensics: binwalk, strings, exiftool\n"""
            ),
        }
        for name, (cat, content) in defaults.items():
            self._skills[name] = Skill(name=name, path="default", content=content, category=cat, loaded_at=datetime.now())
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

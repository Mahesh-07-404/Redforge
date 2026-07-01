"""Skill loader for agent instructions and knowledge"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from redforge.skills.loader import DynamicSkillLoader
from redforge.skills.registry import SkillMetadata, SkillRegistry


@dataclass
class Skill:
    name: str
    path: str
    content: str
    category: str
    mode: str | None = None
    difficulty: str = "intermediate"
    tags: list[str] = field(default_factory=list)
    loaded_at: datetime | None = None


class SkillLoader:
    """Loads and manages skill files for the agent (V2 wrapper)"""

    _DEFAULT_SKILLS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "skills"

    def __init__(self, skills_dir: str | None = None):
        self.skills_dir = Path(skills_dir) if skills_dir else self._DEFAULT_SKILLS_DIR
        self.registry = SkillRegistry(str(self.skills_dir))
        self.loader = DynamicSkillLoader(self.registry)
        self._loaded = False

    @property
    def _skills(self) -> dict[str, Skill]:
        # Wrap the registry's SkillMetadata into Skill objects for backward compatibility
        result = {}
        for k, s in self.registry.skills.items():
            result[k] = Skill(
                name=s.name,
                path=s.path,
                content=s.content,
                category=s.category,
                mode=s.mode,
                tags=s.tags,
            )
        return result

    @_skills.setter
    def _skills(self, value: dict[str, Any]) -> None:
        self.registry.skills = {}
        for k, v in value.items():
            if isinstance(v, Skill):
                self.registry.skills[k] = SkillMetadata(
                    name=v.name,
                    path=v.path,
                    content=v.content,
                    category=v.category,
                    mode=v.mode,
                    tags=v.tags,
                )
            elif isinstance(v, SkillMetadata):
                self.registry.skills[k] = v
            else:
                # Direct dict or other mock object
                self.registry.skills[k] = SkillMetadata(
                    name=getattr(v, "name", k),
                    path=getattr(v, "path", "default"),
                    content=getattr(v, "content", ""),
                    category=getattr(v, "category", "SYSTEM"),
                    mode=getattr(v, "mode", None),
                    tags=getattr(v, "tags", []),
                )

    def load_skills(self) -> None:
        """Load all skill files from the skills directory"""
        if not self.skills_dir.exists():
            self._create_default_skills()
            return
        self.registry.load_registry()
        self._loaded = True

    def _create_default_skills(self) -> None:
        """Minimal built-in skills when skills directory is missing"""
        defaults = {
            "SYSTEM/persona": (
                "SYSTEM",
                """## RedForge Agent\nAutonomous pentesting AI. Always verify scope. Document findings. Non-destructive first.\n""",
            ),
            "MODES/bugbounty": (
                "MODES",
                """## Bug Bounty Recon\npassive: whois, dns, certs\nactive: nmap, ffuf, subfinder\nvulns: sqli, xss, ssrf, idor\n""",
            ),
            "MODES/ctf": (
                "MODES",
                """## CTF Approach\nWeb: sqli, xss, lfi, idor\nBinary: gdb, pwntools, ropper\nCrypto: padding oracle, xor, rsa\nForensics: binwalk, strings, exiftool\n""",
            ),
        }
        self.registry.skills = {}
        for name, (cat, content) in defaults.items():
            mode = "BUGBOUNTY" if "bugbounty" in name else ("CTF" if "ctf" in name else None)
            self.registry.skills[name] = SkillMetadata(
                name=name, path="default", content=content, category=cat, mode=mode
            )
        self._loaded = True

    def get_context_for_mode(self, mode: str) -> str:
        """Get all loaded skill text relevant to a mode"""
        if not self._loaded:
            self.load_skills()
        mode_key = mode.lower()
        parts = []
        for s in self.registry.list_skills():
            if (
                mode_key in s.name.lower()
                or mode_key in s.category.lower()
                or (s.mode and mode_key in s.mode.lower())
            ):
                parts.append(f"\n\n### [{s.category}] {s.name}\n{s.content}")

        if not parts:
            for s in self.registry.list_skills():
                if s.category == "SYSTEM":
                    parts.append(f"\n\n### {s.name}\n{s.content}")
        return "\n".join(parts) if parts else "No skill context available."

    def get_top_k(self, query: str, k: int = 5) -> str:
        """Return top-k skills most relevant to a query (keyword-scored)"""
        if not self._loaded:
            self.load_skills()
        query_tokens = set(query.lower().split())
        scored: list[tuple] = []

        for s in self.registry.list_skills():
            blob = (s.name + " " + s.content + " " + s.category).lower()
            score = sum(1.0 for tok in query_tokens if tok in blob)
            if s.category == "SYSTEM" or s.category == "TOOLS":
                score += 0.3
            if score > 0:
                scored.append((score, s))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for _, s in scored[:k]:
            snippet = s.content[:700] + ("\n[...truncated]" if len(s.content) > 700 else "")
            results.append(f"### [{s.category}] {s.name}\n{snippet}")
        return "\n\n".join(results)

    def get_hierarchical_context(self, active_mode: str, intent: str, query: str) -> str:
        if not self._loaded:
            self.load_skills()
        selected = self.loader.select_skills(intent, active_mode, query)
        return self.loader.build_context(selected, active_mode, intent)

    def get_skill(self, name: str) -> Skill | None:
        if not self._loaded:
            self.load_skills()
        s = self.registry.get_skill(name)
        if s:
            return Skill(
                name=s.name,
                path=s.path,
                content=s.content,
                category=s.category,
                mode=s.mode,
                tags=s.tags,
            )
        return None

    def list_skills(self, category: str | None = None) -> list[Skill]:
        if not self._loaded:
            self.load_skills()
        skills = []
        for s in self.registry.list_skills():
            if category and s.category.upper() != category.upper():
                continue
            skills.append(
                Skill(
                    name=s.name,
                    path=s.path,
                    content=s.content,
                    category=s.category,
                    mode=s.mode,
                    tags=s.tags,
                )
            )
        return skills

    def search_skills(self, query: str) -> list[Skill]:
        if not self._loaded:
            self.load_skills()
        q = query.lower()
        skills = []
        for s in self.registry.list_skills():
            if q in s.name.lower() or q in s.content.lower():
                skills.append(
                    Skill(
                        name=s.name,
                        path=s.path,
                        content=s.content,
                        category=s.category,
                        mode=s.mode,
                        tags=s.tags,
                    )
                )
        return skills

    def is_loaded(self) -> bool:
        return self._loaded

    def reload(self) -> None:
        self._loaded = False
        self.load_skills()

    def stats(self) -> dict[str, Any]:
        by_cat: dict[str, int] = {}
        for s in self.registry.list_skills():
            by_cat[s.category] = by_cat.get(s.category, 0) + 1
        return {
            "skills_dir": str(self.skills_dir),
            "dir_exists": self.skills_dir.exists(),
            "total": len(self.registry.skills),
            "by_category": by_cat,
        }

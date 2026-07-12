"""Skill indexing system for agent knowledge retrieval"""

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from redforge.memory.vector import (
    MemoryEntry,
    SearchResult,
    create_vector_store,
)

logger = logging.getLogger(__name__)


class SkillCategory(str, Enum):
    SYSTEM = "system"
    AUTONOMY = "autonomy"
    BUGBOUNTY = "bugbounty"
    CTF = "ctf"
    LEARNING = "learning"
    CODING = "coding"
    ANDROID = "android"
    TOOLS = "tools"
    SAFETY = "safety"
    LLM = "llm"
    GENERAL = "general"
    CYBERSECURITY = "cybersecurity"


@dataclass
class SkillEntry:
    name: str
    path: str
    content: str
    category: str
    mode: str | None = None
    difficulty: str = "intermediate"
    tags: list[str] = field(default_factory=list)
    summary: str = ""


class SkillIndexer:
    """Indexes skill files for semantic retrieval"""

    def __init__(
        self,
        skills_dir: str | None = None,
        persist_dir: str = "./workspaces",
        vector_db: str = "simple",
    ):
        if skills_dir:
            self.skills_dir = Path(skills_dir)
        else:
            self.skills_dir = Path(__file__).parent.parent.parent / "skills"

        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.vector_store = create_vector_store(
            vector_db=vector_db,
            persist_dir=str(self.persist_dir / "skills_index"),
            collection_name="skills",
        )

        self._skills_index: dict[str, SkillEntry] = {}
        self._index_file = self.persist_dir / "skills_index" / "skills_manifest.json"
        self._load_manifest()

    def _load_manifest(self) -> None:
        """Load skill manifest"""
        if self._index_file.exists():
            try:
                with open(self._index_file) as f:
                    data = json.load(f)
                    for skill_data in data.get("skills", []):
                        skill = SkillEntry(**skill_data)
                        self._skills_index[skill.path] = skill
            except (
                OSError,
                ValueError,
                TypeError,
            ) as exc:  # nosec B110 - best-effort manifest load
                logger.debug("Failed to load skills manifest from '%s': %s", self._index_file, exc)

    def _save_manifest(self) -> None:
        """Save skill manifest"""
        self._index_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._index_file, "w") as f:
            json.dump(
                {
                    "skills": [
                        {
                            "name": s.name,
                            "path": s.path,
                            "content": s.content,
                            "category": s.category,
                            "mode": s.mode,
                            "difficulty": s.difficulty,
                            "tags": s.tags,
                            "summary": s.summary,
                        }
                        for s in self._skills_index.values()
                    ],
                    "last_updated": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

    def index_skills(self) -> int:
        """Index all skill files (both new cybersecurity skills and legacy archive)"""
        self._skills_index.clear()
        entries = []
        count = 0

        # 1. Index current skills directory
        if self.skills_dir.exists():
            for root, _dirs, files in os.walk(self.skills_dir):
                root_path = Path(root)
                # Skip legacy archive if mapped nestedly (we load it separately below)
                if "archive" in root_path.parts:
                    continue
                for file in files:
                    if file.endswith((".md", ".txt")):
                        file_path = root_path / file
                        try:
                            skill = self._parse_skill_file(
                                file_path, self.skills_dir, is_legacy=False
                            )
                            if skill:
                                self._skills_index[skill.path] = skill
                                entry = MemoryEntry(
                                    id=hashlib.md5(
                                        skill.path.encode(), usedforsecurity=False
                                    ).hexdigest(),
                                    content=skill.content,
                                    metadata={
                                        "name": skill.name,
                                        "category": skill.category,
                                        "mode": skill.mode,
                                        "difficulty": skill.difficulty,
                                        "tags": skill.tags,
                                    },
                                    entry_type="skill",
                                )
                                entries.append(entry)
                                count += 1
                        except Exception as e:
                            logger.debug("Error indexing %s: %s", file_path, e)

        # 2. Index legacy archive directory
        legacy_dir = self.skills_dir.parent / "archive" / "legacy_skills"
        if legacy_dir.exists():
            for root, _dirs, files in os.walk(legacy_dir):
                root_path = Path(root)
                for file in files:
                    if file.endswith((".md", ".txt")):
                        file_path = root_path / file
                        try:
                            skill = self._parse_skill_file(file_path, legacy_dir, is_legacy=True)
                            if skill:
                                self._skills_index[skill.path] = skill
                                entry = MemoryEntry(
                                    id=hashlib.md5(
                                        skill.path.encode(), usedforsecurity=False
                                    ).hexdigest(),
                                    content=skill.content,
                                    metadata={
                                        "name": skill.name,
                                        "category": skill.category,
                                        "mode": skill.mode,
                                        "difficulty": skill.difficulty,
                                        "tags": skill.tags,
                                    },
                                    entry_type="skill",
                                )
                                entries.append(entry)
                                count += 1
                        except Exception as e:
                            logger.debug("Error indexing legacy %s: %s", file_path, e)

        if entries:
            self.vector_store.add(entries)

        self._save_manifest()
        return count

    def _parse_skill_file(
        self, file_path: Path, base_path: Path, is_legacy: bool = False
    ) -> SkillEntry | None:
        """Parse a skill file"""
        try:
            with open(file_path, encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Parse YAML frontmatter
            metadata: dict[str, Any] = {}
            content_body = content

            frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
            if frontmatter_match:
                try:
                    metadata = yaml.safe_load(frontmatter_match.group(1)) or {}
                    content_body = content[frontmatter_match.end() :]
                except Exception as exc:
                    logger.debug("Failed to parse frontmatter in '%s': %s", file_path, exc)

            relative_path = str(file_path.relative_to(base_path))
            parts = relative_path.split(os.sep)

            # Derive true name
            name = metadata.get("name")
            if not name:
                if file_path.stem.upper() == "SKILL" and len(parts) > 1:
                    name = parts[-2]
                else:
                    name = file_path.stem
            name = name.replace("_", " ").replace("-", " ").title()

            # Derive category and mode
            category = (
                metadata.get("category") or metadata.get("subdomain") or metadata.get("domain")
            )
            if not category:
                if is_legacy:
                    category = parts[0] if len(parts) > 1 else "general"
                else:
                    category = "cybersecurity"
            category = category.upper()

            mode = metadata.get("mode") or metadata.get("subdomain")
            if mode:
                mode = mode.upper()

            summary = metadata.get("description") or content_body[:200].replace("\n", " ").strip()

            tags_raw = metadata.get("tags", [])
            if isinstance(tags_raw, str):
                tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
            else:
                tags = [str(t) for t in tags_raw if t is not None]

            if "sql" in content.lower() and "sql" not in tags:
                tags.append("sql")
            if "xss" in content.lower() and "xss" not in tags:
                tags.append("xss")

            difficulty = "intermediate"
            if any(
                word in content.lower() for word in ["basic", "beginner", "intro", "fundamentals"]
            ):
                difficulty = "beginner"
            elif any(word in content.lower() for word in ["advanced", "expert", "complex"]):
                difficulty = "advanced"

            return SkillEntry(
                name=name,
                path=relative_path,
                content=content_body,
                category=category,
                mode=mode,
                difficulty=difficulty,
                tags=tags,
                summary=summary,
            )
        except Exception as e:
            logger.debug("Error parsing %s: %s", file_path, e)
            return None

    def search_skills(
        self,
        query: str,
        category: str | None = None,
        mode: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search skills by query"""
        # Retrieve and render the RAG query optimizer template
        from redforge.prompt_library.registry import get_prompt_library_registry
        from redforge.prompts.registry import get_prompt_registry

        try:
            registry = get_prompt_registry()
            rendered = registry.render(
                "rag_search_optimizer",
                user_query=query,
                context_focus=category or "cybersecurity",
            )
            logger.debug("Rendered RAG search optimizer prompt:\n%s", rendered)
        except Exception as e:
            logger.debug("Failed to render RAG optimizer prompt: %s", e)

        try:
            lib_registry = get_prompt_library_registry()
            rendered_gen = lib_registry.render(
                "rag_retrieval_refiner", query_text=query, search_domain=category or "general"
            )
            logger.debug("Rendered general RAG retrieval refiner prompt:\n%s", rendered_gen)
        except Exception as e:
            logger.debug("Failed to render general RAG refiner prompt: %s", e)

        results = self.vector_store.search(query, limit=limit)

        if category or mode:
            filtered = []
            for result in results:
                if category and result.metadata.get("category") != category:
                    continue
                if mode and result.metadata.get("mode") != mode:
                    continue
                filtered.append(result)
            return filtered

        return results

    def get_skills_by_category(self, category: str) -> list[SkillEntry]:
        """Get all skills in a category"""
        return [s for s in self._skills_index.values() if s.category.lower() == category.lower()]

    def get_skills_by_mode(self, mode: str) -> list[SkillEntry]:
        """Get all skills for a mode"""
        return [s for s in self._skills_index.values() if s.mode and s.mode.lower() == mode.lower()]

    def get_context_for_task(self, task: str, mode: str | None = None, max_skills: int = 5) -> str:
        """Get relevant skill context for a task"""
        results = self.search_skills(task, mode=mode, limit=max_skills)

        context_parts = ["## Relevant Skills\n"]

        for result in results:
            skill = self._skills_index.get(result.metadata.get("name", ""))
            if skill:
                context_parts.append(f"### {skill.name} ({skill.category})\n")
                context_parts.append(f"{skill.content[:500]}...\n\n")

        return "\n".join(context_parts)

    def get_all_skills(self) -> list[SkillEntry]:
        """Get all indexed skills"""
        return list(self._skills_index.values())

    def get_stats(self) -> dict[str, Any]:
        """Get indexing statistics"""
        categories: dict[str, int] = {}
        modes: dict[str, int] = {}

        for skill in self._skills_index.values():
            categories[skill.category] = categories.get(skill.category, 0) + 1
            if skill.mode:
                modes[skill.mode] = modes.get(skill.mode, 0) + 1

        return {
            "total_skills": len(self._skills_index),
            "categories": categories,
            "modes": modes,
            "indexed_entries": len(self.vector_store.list_entries()),
            "vector_store_available": self.vector_store.is_available,
            "skills_dir": str(self.skills_dir),
        }

    def create_default_skills(self) -> int:
        """Create default skill files if none exist"""
        if self.skills_dir.exists() and any(self.skills_dir.rglob("*.md")):
            return 0

        self.skills_dir.mkdir(parents=True, exist_ok=True)
        count = 0

        default_skills = {
            "SYSTEM/01_prompt.md": """# RedForge System Prompt

You are RedForge, an autonomous penetration testing AI agent.

## Your Capabilities
- Bug bounty hunting
- CTF challenge solving
- Security learning
- Vulnerable code generation
- Android pentesting

## Safety Rules
1. Always verify scope
2. Get authorization first
3. Stop if requested
4. Document findings
5. Non-destructive first
""",
            "SYSTEM/02_modes.md": """# Operation Modes

## Bug Bounty Mode
Automated vulnerability hunting with recon, enumeration, and exploitation.

## CTF Mode
Capture The Flag challenges - web, pwn, crypto, forensics.

## Learning Mode
Interactive security education with quizzes and exercises.

## Coding Mode
Generate vulnerable code for learning and create exploits.

## Android Mode
Mobile app security testing with static and dynamic analysis.
""",
            "SAFETY/01_scope.md": """# Scope Verification

Always verify targets are in scope before testing.

1. Check program scope file
2. Verify ownership
3. Document authorization
4. Block out-of-scope targets
""",
            "BUGBOUNTY/01_recon.md": """# Bug Bounty Reconnaissance

## Passive Recon
- WHOIS lookups
- DNS enumeration
- Subdomain discovery
- Certificate transparency

## Active Recon
- Port scanning (nmap)
- Technology detection
- Directory brute-forcing

## Tools
subfinder, amass, naabu, nmap, ffuf
""",
            "CTF/01_web.md": """# CTF Web Challenges

## Common Vulnerabilities
- SQL Injection
- XSS (reflected, stored, DOM)
- SSRF
- File Inclusion (LFI/RFI)
- IDOR

## Approach
1. Enumerate endpoints
2. Test all inputs
3. Check for IDOR
4. Look for business logic flaws
""",
        }

        for path, content in default_skills.items():
            file_path = self.skills_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w") as f:
                f.write(content)
            count += 1

        return count

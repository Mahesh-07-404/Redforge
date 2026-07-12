"""Skill indexing system for agent knowledge retrieval"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

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
        """Index all skill files"""
        if not self.skills_dir.exists():
            return 0

        self._skills_index.clear()
        entries = []
        count = 0

        for root, _dirs, files in os.walk(self.skills_dir):
            root_path = Path(root)

            for file in files:
                if file.endswith((".md", ".txt")):
                    file_path = root_path / file
                    try:
                        skill = self._parse_skill_file(file_path, root_path)
                        if skill:
                            self._skills_index[skill.path] = skill

                            entry = MemoryEntry(
                                id=hashlib.md5(skill.path.encode()).hexdigest(),
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
                        print(f"Error indexing {file_path}: {e}")

        if entries:
            self.vector_store.add(entries)

        self._save_manifest()
        return count

    def _parse_skill_file(self, file_path: Path, base_path: Path) -> SkillEntry | None:
        """Parse a skill file"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            relative_path = str(file_path.relative_to(base_path))
            parts = relative_path.split(os.sep)

            category = parts[0] if len(parts) > 1 else "general"
            mode = parts[1] if len(parts) > 2 else None

            name = file_path.stem.replace("_", " ").replace("-", " ").title()

            summary = content[:200].replace("\n", " ").strip()

            tags = []
            if "sql" in content.lower():
                tags.append("sql")
            if "xss" in content.lower():
                tags.append("xss")
            if "sqli" in content.lower() or "injection" in content.lower():
                tags.append("injection")
            if "recon" in content.lower():
                tags.append("recon")
            if "privesc" in content.lower():
                tags.append("privesc")

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
                content=content,
                category=category,
                mode=mode,
                difficulty=difficulty,
                tags=tags,
                summary=summary,
            )
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def search_skills(
        self,
        query: str,
        category: str | None = None,
        mode: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search skills by query"""
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

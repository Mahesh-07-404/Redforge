"""RedForge Skill Registry"""

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class SkillMetadata:
    name: str
    category: str
    mode: str | None = None
    tags: list[str] = field(default_factory=list)
    priority: int = 5
    token_cost: int = 500
    content: str = ""
    path: str = ""
    version: str = "1.0"
    author: str = ""
    license: str = ""
    nist_csf: list[str] = field(default_factory=list)
    mitre_attack: list[str] = field(default_factory=list)


class SkillRegistry:
    """Registry that loads, catalogs, and indexes skills with metadata"""

    def __init__(self, skills_dir: str | Path | None = None):
        if skills_dir:
            self.skills_dir = Path(skills_dir)
        else:
            # Default to skills/ directory under root
            self.skills_dir = Path(__file__).resolve().parent.parent.parent.parent / "skills"

        self.skills: dict[str, SkillMetadata] = {}
        self._indexer = None

    def load_registry(self) -> None:
        """Scan skills directory and parse metadata/frontmatter from markdown files"""
        self.skills = {}

        if not self.skills_dir.exists():
            return

        # 1. Load cybersecurity skills
        for root, dirs, files in os.walk(self.skills_dir):
            dirs[:] = [
                d for d in dirs if not d.startswith(("__", ".", "cache", "versions", "archive"))
            ]
            for fname in files:
                if fname.endswith(".md"):
                    file_path = Path(root) / fname
                    self._register_file(file_path, is_legacy=False)

        # 2. Load legacy skills for backward compatibility (system, safety, execution)
        legacy_dir = self.skills_dir.parent / "archive" / "legacy_skills"
        if legacy_dir.exists():
            for root, dirs, files in os.walk(legacy_dir):
                dirs[:] = [d for d in dirs if not d.startswith(("__", ".", "cache", "versions"))]
                for fname in files:
                    if fname.endswith(".md"):
                        file_path = Path(root) / fname
                        self._register_file(file_path, is_legacy=True)

        # 3. Index skills automatically for Memory & RAG integration
        try:
            from redforge.config.config import get_settings
            from redforge.memory.skill_index import SkillIndexer

            settings = get_settings()
            indexer = SkillIndexer(
                skills_dir=str(self.skills_dir),
                persist_dir=settings.memory.persist_dir,
                vector_db=settings.memory.vector_db,
            )
            indexer.index_skills()
            self._indexer = indexer
        except Exception as e:
            logger.debug("Failed to index skills: %s", e)

    def _register_file(self, file_path: Path, is_legacy: bool = False) -> None:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except (
            OSError,
            PermissionError,
        ) as exc:  # nosec B110 - best-effort skill file scan; skip unreadable files
            logger.debug("Skipping unreadable skill file '%s': %s", file_path, exc)
            return

        # Parse YAML frontmatter if available
        metadata: dict[str, Any] = {}
        content_body = content

        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if frontmatter_match:
            try:
                metadata = yaml.safe_load(frontmatter_match.group(1)) or {}
                content_body = content[frontmatter_match.end() :]
            except (
                ValueError,
                yaml.YAMLError,
            ) as exc:  # nosec B110 - best-effort YAML frontmatter parse
                logger.debug("Failed to parse frontmatter in '%s': %s", file_path, exc)

        # Apply path-based fallbacks for missing fields
        try:
            relative = file_path.relative_to(self.skills_dir)
        except ValueError:
            try:
                legacy_dir = self.skills_dir.parent / "archive" / "legacy_skills"
                relative = file_path.relative_to(legacy_dir)
            except ValueError:
                relative = Path(file_path.name)

        parts = relative.parts
        category = metadata.get("category") or metadata.get("subdomain") or metadata.get("domain")

        if is_legacy:
            if not category:
                first_line = content.strip().split("\n")[0] if content.strip() else ""
                match = re.match(r"^#\s*([A-Za-z\s]+?)(?:\s+Skill|\s+SYSTEM)?\s*:", first_line)
                if match:
                    lbl = match.group(1).strip().upper()
                    if lbl in ("CORE SYSTEM", "CORE"):
                        category = "SYSTEM"
                    elif lbl == "MODE":
                        category = "MODES"
                    elif lbl in ("SAFETY", "SYSTEM", "MODES", "TOOLS", "EXECUTION"):
                        category = lbl

                if not category:
                    if len(parts) > 1:
                        if parts[0].lower() == "domain" and len(parts) > 2:
                            category = parts[1].upper()
                        else:
                            category = parts[0].upper()
                    else:
                        category = "GENERAL"
        else:
            if not category:
                category = "CYBERSECURITY"

        # Determine mode
        mode = metadata.get("mode") or metadata.get("subdomain")
        if is_legacy and not mode and category.upper() == "MODES":
            if parts[0].lower() == "domain" and len(parts) > 2:
                mode = Path(parts[2]).stem.upper()
            elif len(parts) > 2:
                mode = parts[1].upper()
            else:
                mode = file_path.stem.upper()

        if mode:
            mode = mode.upper()

        tags_raw = metadata.get("tags", [])
        if isinstance(tags_raw, str):
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        else:
            tags = [str(t) for t in tags_raw if t is not None]

        # Determine true name
        name = metadata.get("name")
        if not name:
            if file_path.stem.upper() == "SKILL" and len(parts) > 1:
                name = parts[-2]
            else:
                name = file_path.stem
        # Clean name format
        name = name.replace("_", " ").replace("-", " ").title()

        priority = int(metadata.get("priority", 5))
        token_cost = int(metadata.get("token_cost", len(content_body.split())))
        version = str(metadata.get("version", "1.0"))
        author = str(metadata.get("author", ""))
        license_str = str(metadata.get("license", ""))
        nist_csf = list(metadata.get("nist_csf", []))
        mitre_attack = list(metadata.get("mitre_attack", []))

        skill = SkillMetadata(
            name=name,
            category=category.upper(),
            mode=mode,
            tags=tags,
            priority=priority,
            token_cost=token_cost,
            content=content_body,
            path=str(file_path),
            version=version,
            author=author,
            license=license_str,
            nist_csf=nist_csf,
            mitre_attack=mitre_attack,
        )
        self.skills[name] = skill

    def get_skill(self, name: str) -> SkillMetadata | None:
        return self.skills.get(name)

    def list_skills(self) -> list[SkillMetadata]:
        return list(self.skills.values())

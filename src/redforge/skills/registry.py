"""RedForge Skill Registry"""

import os
import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

@dataclass
class SkillMetadata:
    name: str
    category: str
    mode: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    priority: int = 5
    token_cost: int = 500
    content: str = ""
    path: str = ""

class SkillRegistry:
    """Registry that loads, catalogs, and indexes skills with metadata"""

    def __init__(self, skills_dir: Optional[str] = None):
        if skills_dir:
            self.skills_dir = Path(skills_dir)
        else:
            # Default to skills/ directory under root
            self.skills_dir = Path(__file__).resolve().parent.parent.parent.parent / "skills"
            
        self.skills: Dict[str, SkillMetadata] = {}

    def load_registry(self) -> None:
        """Scan skills directory and parse metadata/frontmatter from markdown files"""
        if not self.skills_dir.exists():
            return

        self.skills = {}
        for root, dirs, files in os.walk(self.skills_dir):
            dirs[:] = [d for d in dirs if not d.startswith(("__", ".", "cache", "versions", "adaptive"))]
            for fname in files:
                if fname.endswith(".md"):
                    file_path = Path(root) / fname
                    self._register_file(file_path)

    def _register_file(self, file_path: Path) -> None:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return

        # Parse YAML frontmatter if available
        metadata: Dict[str, Any] = {}
        content_body = content
        
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if frontmatter_match:
            try:
                metadata = yaml.safe_load(frontmatter_match.group(1)) or {}
                content_body = content[frontmatter_match.end():]
            except Exception:
                pass

        # Apply path-based fallbacks for missing fields
        try:
            relative = file_path.relative_to(self.skills_dir)
        except ValueError:
            relative = Path(file_path.name)

        parts = relative.parts
        category = metadata.get("category") or (parts[0].upper() if len(parts) > 1 else "GENERAL")
        
        # If it's a MODES folder, parse the mode
        mode = metadata.get("mode")
        if not mode and category.upper() == "MODES":
            if len(parts) > 2:
                mode = parts[1].upper()
            else:
                mode = file_path.stem.upper()
        elif mode:
            mode = mode.upper()

        tags_raw = metadata.get("tags", [])
        if isinstance(tags_raw, str):
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        else:
            tags = list(tags_raw)

        name = metadata.get("name") or ("/".join(list(parts[:-1]) + [file_path.stem]) if len(parts) > 1 else file_path.stem)
        priority = int(metadata.get("priority", 5))
        token_cost = int(metadata.get("token_cost", len(content_body.split())))

        skill = SkillMetadata(
            name=name,
            category=category.upper(),
            mode=mode,
            tags=tags,
            priority=priority,
            token_cost=token_cost,
            content=content_body,
            path=str(file_path),
        )
        self.skills[name] = skill

    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        return self.skills.get(name)

    def list_skills(self) -> List[SkillMetadata]:
        return list(self.skills.values())

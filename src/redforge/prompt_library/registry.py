"""Registry and loader for RedForge General Prompt Library"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class GeneralPromptTemplate:
    id: str
    name: str
    description: str
    category: str
    tags: list[str] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    template: str = ""
    examples: list[dict[str, Any]] = field(default_factory=list)


class PromptLibraryRegistry:
    """Manages discovery, caching, validation, and rendering of general prompt templates"""

    def __init__(self, templates_dir: str | Path | None = None):
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = Path(__file__).resolve().parent / "templates"

        self.prompts: dict[str, GeneralPromptTemplate] = {}
        self.load_prompts()

    def load_prompts(self) -> None:
        """Scan and load all yaml prompt templates from the directory structure"""
        self.prompts = {}
        if not self.templates_dir.exists():
            return

        for root, _, files in os.walk(self.templates_dir):
            for file in files:
                if file.endswith((".yaml", ".yml")):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, encoding="utf-8", errors="replace") as f:
                            data = yaml.safe_load(f)
                        if data and "id" in data and "template" in data:
                            prompt = GeneralPromptTemplate(
                                id=data["id"],
                                name=data.get("name", file_path.stem.title()),
                                description=data.get("description", ""),
                                category=data.get("category", "utilities"),
                                tags=list(data.get("tags", [])),
                                variables=list(data.get("variables", [])),
                                template=data["template"],
                                examples=list(data.get("examples", [])),
                            )
                            self.prompts[prompt.id] = prompt
                    except Exception as e:
                        logger.debug("Failed to load prompt template from '%s': %s", file_path, e)

    def get_prompt(self, prompt_id: str) -> GeneralPromptTemplate:
        """Retrieve a specific prompt template by its ID"""
        if prompt_id not in self.prompts:
            raise KeyError(f"Prompt template '{prompt_id}' not found in registry")
        return self.prompts[prompt_id]

    def render(self, prompt_id: str, **kwargs) -> str:
        """Render a prompt template with provided keyword variables"""
        prompt = self.get_prompt(prompt_id)
        missing = [v for v in prompt.variables if v not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables for template '{prompt_id}': {missing}")
        return prompt.template.format(**kwargs)

    def get_suitable_prompt(self, intent: str, category: str = None) -> GeneralPromptTemplate:
        """
        Retrieve the most suitable general-purpose prompt template.
        """
        # Map intents to prompt IDs
        intent_map = {
            "GENERAL_CHAT": "chat_general_chat",
            "CHAT": "chat_general_chat",
            "CODING": "coding_developer",
            "LEARNING": "chat_general_chat",
            "DECOMPOSE": "planning_decomposer",
            "REASON": "reasoning_critical_thought",
        }

        pid = intent_map.get(intent.upper())
        if pid and pid in self.prompts:
            return self.prompts[pid]

        if category:
            for p in self.prompts.values():
                if p.category.lower() == category.lower():
                    return p

        # Fallback to chat or reasoning
        fallback_candidates = ["chat_general_chat", "reasoning_critical_thought"]
        for cand in fallback_candidates:
            if cand in self.prompts:
                return self.prompts[cand]

        return GeneralPromptTemplate(
            id="default_general_fallback",
            name="Default General Fallback",
            description="System fallback general prompt",
            category="chat",
            template="You are RedForge, an autonomous assistant. Help the user. Context: {query}",
            variables=["query"],
        )


# Global singleton
_global_library_registry = None


def get_prompt_library_registry() -> PromptLibraryRegistry:
    global _global_library_registry
    if _global_library_registry is None:
        _global_library_registry = PromptLibraryRegistry()
    return _global_library_registry

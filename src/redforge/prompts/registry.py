"""Registry and loader for RedForge Prompt Library"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    id: str
    name: str
    description: str
    category: str
    tags: list[str] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    template: str = ""
    examples: list[dict[str, Any]] = field(default_factory=list)


class PromptRegistry:
    """Manages discovery, caching, validation, and rendering of prompt templates"""

    def __init__(self, templates_dir: str | Path | None = None):
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = Path(__file__).resolve().parent / "templates"

        self.prompts: dict[str, PromptTemplate] = {}
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
                            prompt = PromptTemplate(
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

    def get_prompt(self, prompt_id: str) -> PromptTemplate:
        """Retrieve a specific prompt template by its ID"""
        if prompt_id not in self.prompts:
            raise KeyError(f"Prompt template '{prompt_id}' not found in registry")
        return self.prompts[prompt_id]

    def render(self, prompt_id: str, **kwargs) -> str:
        """Render a prompt template with provided keyword variables"""
        prompt = self.get_prompt(prompt_id)
        # Validate that all required variables are supplied
        missing = [v for v in prompt.variables if v not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables for template '{prompt_id}': {missing}")
        return prompt.template.format(**kwargs)

    def get_suitable_prompt(self, intent: str, category: str = None) -> PromptTemplate:
        """
        Retrieve the most suitable prompt template based on intent and optional category.
        Falls back to a general reasoning/utility prompt if no match.
        """
        # Map intents to prompt IDs
        intent_map = {
            "RECON": "recon_passive_active",
            "SCAN": "recon_passive_active",
            "EXPLOIT": "web_vuln_scanner",
            "WEB": "web_vuln_scanner",
            "API": "api_endpoint_audit",
            "NETWORK": "network_subnet_scan",
            "CLOUD": "cloud_resource_auditor",
            "MOBILE": "mobile_apk_analyst",
            "OSINT": "osint_passive_gatherer",
            "REPORT": "reporting_finding_consolidator",
            "CHAT": "reasoning_thought_loop",
            "LEARNING": "reasoning_thought_loop",
            "CODING": "reasoning_thought_loop",
        }

        pid = intent_map.get(intent.upper())
        if pid and pid in self.prompts:
            return self.prompts[pid]

        # Search by category
        if category:
            for p in self.prompts.values():
                if p.category.lower() == category.lower():
                    return p

        # Final default fallback
        fallback_candidates = ["reasoning_thought_loop", "planning_dynamic_plan"]
        for cand in fallback_candidates:
            if cand in self.prompts:
                return self.prompts[cand]

        # In-memory default in case directory scan fails or is empty
        return PromptTemplate(
            id="default_fallback",
            name="Default Fallback",
            description="System fallback prompt",
            category="utilities",
            template="Analyze current state and formulate next steps. Context: {context}. Query: {query}",
            variables=["context", "query"],
        )


# Global singleton instance for easy imports and sharing
_global_registry = None


def get_prompt_registry() -> PromptRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = PromptRegistry()
    return _global_registry

"""Planning and prompt orchestration service for RedForge."""

import logging
from typing import Any

from redforge.prompts.registry import get_prompt_registry

from ..contracts.intent import ParsedIntent
from ..contracts.session import SessionState

logger = logging.getLogger(__name__)


class PlannerService:
    """Service to orchestrate prompt templates, plans, and next steps for the agent."""

    def build_system_prompt(
        self, session: SessionState, intent: ParsedIntent, skills_context: str, memory_context: str
    ) -> str:
        """Constructs the system instructions for the LLM based on current target, mode, and skills."""
        registry = get_prompt_registry()
        # Automatically retrieve the most suitable prompt based on user intent and context
        prompt_tmpl = registry.get_suitable_prompt(intent.intent_type.value)

        # Merge the retrieved prompt template with active target instructions, skills context, and memory context
        base_prompt = prompt_tmpl.template

        return f"""You are RedForge, an elite autonomous penetration testing agent.
Active Mode: {session.mode}
Autonomy Level: {session.autonomy}
Target: {session.target or "NONE"}

## BASE WORKFLOW & METHODOLOGY
{base_prompt}

## SKILLS & GUIDELINES
{skills_context}

## DISCOVERED CONTEXT
{memory_context}

## TARGET INSTRUCTIONS
1. Analyze the objective.
2. Maintain target consistency: ONLY interact with {session.target or "nothing"}.
3. To run a tool, use the format:
TOOL: <name>
COMMAND: <cmd>
4. If you find vulnerabilities, record them as FINDING: blocks.
5. Provide a final summary when the task is done.
"""

    def generate_plan(self, session: SessionState, intent: ParsedIntent) -> list[dict[str, Any]]:
        """Generates a structured list of tasks/phases for the current session."""
        # Retrieve and render the dynamic planner template
        try:
            registry = get_prompt_registry()
            rendered = registry.render(
                "planning_dynamic_plan",
                target=session.target or "NONE",
                scope=session.scope or "Default Authorization Rule",
                intent=intent.intent_type.value,
            )
            logger.debug("Rendered dynamic planner template:\n%s", rendered)
        except Exception as e:
            logger.debug("Failed to render planner template: %s", e)

        # Retrieve and render the general task decomposer template
        from redforge.prompt_library.registry import get_prompt_library_registry

        try:
            lib_registry = get_prompt_library_registry()
            rendered_gen = lib_registry.render(
                "planning_decomposer",
                goal=f"Generate plan for target {session.target or 'NONE'}",
                constraints=f"Scope policy: {session.scope or 'Default Authorization Rule'}",
            )
            logger.debug("Rendered task decomposer template:\n%s", rendered_gen)
        except Exception as e:
            logger.debug("Failed to render task decomposer: %s", e)

        # Clean modular placeholder for structural planning
        return [
            {
                "id": "recon",
                "description": f"Perform initial reconnaissance on {session.target}",
                "status": "pending",
            },
            {
                "id": "scan",
                "description": f"Scan active services on {session.target}",
                "status": "pending",
            },
            {
                "id": "exploit",
                "description": "Identify and verify vulnerabilities",
                "status": "pending",
            },
            {"id": "report", "description": "Compile final findings report", "status": "pending"},
        ]

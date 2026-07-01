"""Planning and prompt orchestration service for RedForge."""

from typing import Any

from ..contracts.intent import ParsedIntent
from ..contracts.session import SessionState


class PlannerService:
    """Service to orchestrate prompt templates, plans, and next steps for the agent."""

    def build_system_prompt(
        self, session: SessionState, intent: ParsedIntent, skills_context: str, memory_context: str
    ) -> str:
        """Constructs the system instructions for the LLM based on current target, mode, and skills."""
        return f"""You are RedForge, an elite autonomous penetration testing agent.
Active Mode: {session.mode}
Autonomy Level: {session.autonomy}
Target: {session.target or "NONE"}

## SKILLS & GUIDELINES
{skills_context}

## DISCOVERED CONTEXT
{memory_context}

## INSTRUCTIONS
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

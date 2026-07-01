from .planner_context import PlannerContext


class PlannerValidator:
    def validate(self, context: PlannerContext) -> list[str]:
        errors = []

        # 1. Session exists
        if not context.active_session:
            errors.append("Validation failed: Active session is missing.")

        # 2. Intent is valid
        if not context.intent:
            errors.append("Validation failed: Intent is missing.")
        elif not context.intent.intent_type or context.intent.intent_type.value == "unknown":
            errors.append("Validation failed: Intent type is invalid or unknown.")

        # 3. Target exists (only if required)
        from ..contracts.intent import IntentType

        security_intents = {
            IntentType.BUG_BOUNTY,
            IntentType.PENTEST,
            IntentType.CTF,
            IntentType.SCAN,
            IntentType.RECON,
            IntentType.EXPLOIT,
        }
        if context.intent and context.intent.intent_type in security_intents:
            target_val = context.target or (
                context.active_session.target if context.active_session else ""
            )
            if not target_val:
                errors.append("Validation failed: Target is required for security tasks.")

        return errors

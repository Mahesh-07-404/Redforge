import asyncio
import logging
from datetime import datetime
from typing import Any

from ..contracts.intent import IntentType
from ..contracts.tool import ToolCall, VerificationStatus
from ..memory.manager import MemoryService as MemoryManager
from ..providers import LLMProvider
from ..reports.engine import ReportService as ReportEngine
from ..skills.loader import SkillService as DynamicSkillLoader
from ..tools.manager import ToolService as ToolExecutor
from ..tools.parser import parse_tool_calls
from .intent import IntentService as IntentEngine
from .safety import SafetyService as SafetyEngine
from .session import SessionService as SessionManager
from .verifier import HallucinationGuard
from .verifier import VerificationService as Verifier

logger = logging.getLogger(__name__)

# Moved to FindingsService


class Pipeline:
    """
    Orchestrates the RedForge pipeline according to the Phase 2 Architecture.

    Flow:
    Intent Engine -> Session/Memory/Safety -> Skill Loader/Context -> LLM -> Executor/Verifier -> Report/Memory
    """

    def __init__(
        self,
        session_manager: SessionManager,
        memory_manager: MemoryManager,
        skill_loader: DynamicSkillLoader,
        intent_engine: IntentEngine,
        tool_executor: ToolExecutor,
        verifier: Verifier,
        report_engine: ReportEngine,
        safety_engine: SafetyEngine,
        llm_provider: LLMProvider,
    ):
        self.session_manager = session_manager
        self.memory_manager = memory_manager
        self.skill_loader = skill_loader
        self.intent_engine = intent_engine
        self.tool_executor = tool_executor
        self.verifier = verifier
        self.report_engine = report_engine
        self.safety_engine = safety_engine
        self.llm_provider = llm_provider
        self.hallucination_guard = HallucinationGuard()

        from .planner import PlannerService

        self.planner = PlannerService()
        from ..findings.engine import FindingsService

        self.findings_service = FindingsService()

    async def process_turn(
        self,
        raw_input: str,
        session_id: str,
        mode: str | None = None,
        target: str | None = None,
        autonomy: str | None = None,
        token_callback: Any | None = None,
        event_callback: Any | None = None,
    ) -> dict[str, Any]:
        """Process a single turn in the pipeline (potentially multiple iterations)."""
        session = self.session_manager.load(session_id)
        if not session:
            # Auto-create the session if it doesn't exist
            m = getattr(mode, "value") if hasattr(mode, "value") else (mode if mode else "bugbounty")
            t = getattr(target, "value") if hasattr(target, "value") else (target if target else None)
            a = (
                getattr(autonomy, "value")
                if hasattr(autonomy, "value")
                else (autonomy if autonomy else "manual")
            )
            session = self.session_manager.create(
                mode=m, target=t, autonomy=a, session_id=session_id
            )

        # Initialize or load ConversationContext
        from ..contracts.conversation import ConversationContext
        from ..providers.base import Message

        meta = session.metadata or {}
        context = ConversationContext(
            active_session=session,
            active_target=session.target,
            current_goal=meta.get("current_goal"),
            conversation_summary=meta.get("conversation_summary"),
            previous_messages=[
                Message(**m) if isinstance(m, dict) else m
                for m in meta.get("previous_messages", [])
            ],
        )

        # 1. Intent Engine
        intent = self.intent_engine.process(raw_input, session.mode, session_id, session.autonomy)
        context.current_intent = intent

        # 2. Session/Target update
        if intent.target and (intent.target != context.active_target):
            intent.target_changed = True
            self.session_manager.set_target(session_id, intent.target)
            self.memory_manager.flush_session(session_id)
            context.active_target = intent.target
            session.target = intent.target

        # Add user message to history
        context.previous_messages.append(Message(role="user", content=raw_input))

        # Check if we should run the legacy execution workflow or route casually
        should_run_legacy = False
        raw_lower = raw_input.lower()

        if "safe command" in raw_lower or "scan the target" in raw_lower:
            # Running legacy execution workflow
            # Ensure target is present for security workflows
            if not session.target:
                response_text = (
                    "Please specify a target for this security task (e.g. 'on example.com')."
                )
                context.previous_messages.append(Message(role="assistant", content=response_text))
                session.metadata["previous_messages"] = [
                    m.__dict__ if hasattr(m, "__dict__") else m for m in context.previous_messages
                ]
                self.session_manager.save(session)
                return {
                    "status": "success",
                    "intent": intent,
                    "response": response_text,
                    "results": [],
                    "session": session,
                    "total_tokens": 0,
                }
            should_run_legacy = True

        if not should_run_legacy:
            planning_intents = {
                IntentType.BUG_BOUNTY,
                IntentType.PENTEST,
                IntentType.CTF,
                IntentType.LEARNING,
                IntentType.REPORT,
                IntentType.RECON,
                IntentType.SCAN,
            }
            if intent.intent_type in planning_intents:
                from ..planner import Planner, PlannerContext

                planner_ctx = PlannerContext(
                    active_session=session,
                    target=session.target,
                    current_goal=intent.raw_input,
                    intent=intent,
                    active_mode=session.mode,
                )
                planner = Planner()
                try:
                    plan = planner.create_plan(planner_ctx)

                    from ..policy.policy_engine import PolicyEngine

                    policy_eng = PolicyEngine()
                    decision = policy_eng.evaluate_plan(plan, session.target or "")

                    response_text = f"### Execution Plan\n\n**Goal:** {plan.goal}\n"
                    response_text += f"**Estimated Duration:** {plan.estimated_duration} seconds\n"
                    response_text += f"**Confidence:** {plan.confidence}\n\n"
                    response_text += "### Policy Decision\n"
                    response_text += f"**Status:** {decision.status.value}\n"
                    response_text += f"**Risk Level:** {decision.risk_level.value}\n"
                    response_text += f"**Reason:** {decision.reason}\n\n"

                    response_text += "**Tasks:**\n"
                    for idx, t in enumerate(plan.ordered_tasks, 1):
                        deps_str = (
                            f" (Depends on: {', '.join(t.dependencies)})" if t.dependencies else ""
                        )
                        tool_str = f" [Tool: {t.tool_hint}]" if t.tool_hint else ""
                        response_text += (
                            f"{idx}. **{t.title}** - {t.description}{tool_str}{deps_str}\n"
                        )

                    all_warnings = list(plan.warnings)
                    if decision.warnings:
                        all_warnings.extend(decision.warnings)

                    if all_warnings:
                        response_text += "\n**Warnings:**\n"
                        for w in all_warnings:
                            response_text += f"- {w}\n"
                except Exception as e:
                    response_text = f"Planner Error: {str(e)}"

                if event_callback:
                    await event_callback("assistant_start", content="")
                if token_callback:
                    await token_callback(response_text)
                if event_callback:
                    await event_callback("assistant_end", content=response_text)

                context.previous_messages.append(Message(role="assistant", content=response_text))
                session.metadata["previous_messages"] = [
                    m.__dict__ if hasattr(m, "__dict__") else m for m in context.previous_messages
                ]
                self.session_manager.save(session)

                return {
                    "status": "success",
                    "intent": intent,
                    "response": response_text,
                    "results": [],
                    "session": session,
                    "total_tokens": len(response_text.split()) if response_text else 1,
                }

            # Route casually via Intent Router
            from .conversation import ConversationManager
            from .router import IntentRouter

            conv_mgr = ConversationManager(self.llm_provider)
            router = IntentRouter(
                conversation_mgr=conv_mgr,
                session_service=self.session_manager,
                report_engine=self.report_engine,
            )
            response_text = await router.route(
                intent, context, token_callback=token_callback, event_callback=event_callback
            )

            # Save assistant response to history
            context.previous_messages.append(Message(role="assistant", content=response_text))
            session.metadata["previous_messages"] = [
                m.__dict__ if hasattr(m, "__dict__") else m for m in context.previous_messages
            ]
            self.session_manager.save(session)

            return {
                "status": "success",
                "intent": intent,
                "response": response_text,
                "results": [],
                "session": session,
                "total_tokens": len(response_text.split()) if response_text else 1,
            }

        # 3. Safety check
        if intent.target:
            violation = self.safety_engine.check_target(intent.target)
            if violation and violation.blocked:
                return {"status": "blocked", "reason": violation.message, "intent": intent}

        history = [Message(role="user", content=raw_input)]
        all_results = []
        max_iterations = 10
        total_tokens = 0

        for _i in range(max_iterations):
            # 4. Dynamic Skill Loader
            skills = self.skill_loader.select_skills(
                intent.intent_type.value, session.mode, raw_input
            )
            skill_context = self.skill_loader.build_context(
                skills, session.mode, intent.intent_type.value
            )

            # Get RAG memory context
            memory_context = self.memory_manager.get_context_for_llm(raw_input, session_id)

            # 5. LLM Call
            system_prompt = self.planner.build_system_prompt(
                session, intent, skill_context, memory_context
            )
            messages = [Message(role="system", content=system_prompt)] + history

            if event_callback:
                await event_callback("assistant_start", content="")

            use_streaming = False
            try:
                supports = self.llm_provider.supports_streaming()
                if isinstance(supports, bool) and supports:
                    use_streaming = True
            except Exception as exc:  # nosec B110 - best-effort check for streaming support
                logger.debug(
                    "Failed to check if LLM provider supports streaming in pipeline: %s", exc
                )

            if use_streaming:
                content_chunks = []
                async for chunk in self.llm_provider.chat_stream(messages):
                    content_chunks.append(chunk)
                    if token_callback:
                        await token_callback(chunk)
                content = "".join(content_chunks)
                from ..providers.base import ChatResponse

                response = ChatResponse(
                    content=content,
                    model=getattr(self.llm_provider, "model", "fake"),
                    usage={"total_tokens": len(content.split())},
                )
            else:
                response = await self.llm_provider.chat(messages)
                content = response.content

            if response.usage and "total_tokens" in response.usage:
                total_tokens += response.usage["total_tokens"]

            if event_callback:
                await event_callback("assistant_end", content=content)

            findings = self.findings_service.parse_findings(content)
            for f in findings:
                if event_callback:
                    await event_callback("finding", finding=f)

            history.append(Message(role="assistant", content=content))

            # 6. Hallucination Guard (Cross-check text only)
            is_valid, reason = self.hallucination_guard.check(content, session.target)
            if not is_valid:
                history.append(
                    Message(role="user", content=f"Refactor your previous response. {reason}")
                )
                continue

            # 7. Parse Tool Calls
            tool_data = parse_tool_calls(content)
            if not tool_data:
                # Final answer provided
                break

            # 8. Execute and Verify
            turn_results = []
            for t in tool_data:
                # Build ToolCall contract
                call = ToolCall(
                    tool_name=str(t.get("tool") or ""),
                    command=str(t.get("command") or "").split() if "command" in t else [],
                    target=session.target or "",
                    timeout_seconds=60,
                    risk_level=intent.risk_level,
                    session_id=session_id,
                    approved=not intent.requires_approval,
                )

                # Autonomy gate logic
                if intent.requires_approval:
                    if event_callback:
                        await event_callback(
                            "confirmation_required",
                            pending_confirmation={"message": content, "tool_calls": []},
                        )
                    return {
                        "status": "pending_approval",
                        "response": content,
                        "intent": intent,
                        "session": session,
                        "total_tokens": total_tokens,
                    }

                # Execute
                if event_callback:
                    await event_callback(
                        "tool_start",
                        tool=t.get("tool"),
                        command=t.get("command", "").split() if "command" in t else [],
                    )

                tool_result = await asyncio.to_thread(self.tool_executor.execute, call)

                # Verify
                verified = self.verifier.validate(tool_result, session)
                turn_results.append(verified)

                if event_callback:
                    await event_callback(
                        "tool_end",
                        tool=tool_result.tool_name,
                        success=verified.status == VerificationStatus.PASSED,
                        result=verified,
                    )

                # Report & Store
                if verified.status == VerificationStatus.PASSED:
                    self.report_engine.add_finding(verified, session_id)
                    # For now, we wrap verified result into MemoryEntry and store
                    from ..contracts.memory import MemoryEntry

                    entry = MemoryEntry(
                        id=str(datetime.now().timestamp()),
                        content=f"Tool {verified.tool_result.tool_name} found: {verified.facts}",
                        metadata={"verified": True},
                    )
                    self.memory_manager.store(session_id, entry)

                history.append(
                    Message(role="user", content=f"Tool Output: {verified.tool_result.stdout}")
                )

            all_results.extend(turn_results)

        for msg in history[1:]:
            context.previous_messages.append(msg)
        session.metadata["previous_messages"] = [
            m.__dict__ if hasattr(m, "__dict__") else m for m in context.previous_messages
        ]
        self.session_manager.save(session)

        return {
            "status": "success",
            "intent": intent,
            "response": history[-1].content,
            "results": all_results,
            "session": session,
            "total_tokens": total_tokens,
        }

    # Build prompt logic moved to PlannerService
    pass

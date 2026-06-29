from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import asyncio

from .session import SessionService as SessionManager
from ..memory.manager import MemoryService as MemoryManager
from ..skills.loader import SkillService as DynamicSkillLoader
from .intent import IntentService as IntentEngine
from ..tools.manager import ToolService as ToolExecutor
from ..tools.parser import parse_tool_calls
from .verifier import VerificationService as Verifier
from .verifier import HallucinationGuard
from ..reports.engine import ReportService as ReportEngine
from .safety import SafetyService as SafetyEngine
from ..providers import LLMProvider, Message
from ..contracts.intent import ParsedIntent, IntentType
from ..contracts.tool import ToolCall, ToolResult, VerifiedResult, VerificationStatus
from ..contracts.session import SessionState

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
        llm_provider: LLMProvider
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
        mode: Optional[str] = None,
        target: Optional[str] = None,
        autonomy: Optional[str] = None,
        token_callback: Optional[Any] = None,
        event_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Process a single turn in the pipeline (potentially multiple iterations)."""
        session = self.session_manager.load(session_id)
        if not session:
            # Auto-create the session if it doesn't exist
            m = mode.value if hasattr(mode, "value") else (mode if mode else "bugbounty")
            t = target.value if hasattr(target, "value") else (target if target else None)
            a = autonomy.value if hasattr(autonomy, "value") else (autonomy if autonomy else "manual")
            session = self.session_manager.create(
                mode=m,
                target=t,
                autonomy=a,
                session_id=session_id
            )

        # 1. Intent Engine
        intent = self.intent_engine.process(raw_input, session.mode, session_id, session.autonomy)
        
        # 2. Session/Target update
        if intent.target_changed:
            self.session_manager.set_target(session_id, intent.target)
            self.memory_manager.flush_session(session_id)
            session.target = intent.target

        # 3. Safety check
        if intent.target:
            violation = self.safety_engine.check_target(intent.target)
            if violation and violation.blocked:
                return {"status": "blocked", "reason": violation.message, "intent": intent}

        history = [Message(role="user", content=raw_input)]
        all_results = []
        max_iterations = 10
        total_tokens = 0
        
        for i in range(max_iterations):
            # 4. Dynamic Skill Loader
            skills = self.skill_loader.select_skills(intent.intent_type.value, session.mode, raw_input)
            skill_context = self.skill_loader.build_context(skills, session.mode, intent.intent_type.value)
            
            # Get RAG memory context
            memory_context = self.memory_manager.get_context_for_llm(raw_input, session_id)
            
            # 5. LLM Call
            system_prompt = self.planner.build_system_prompt(session, intent, skill_context, memory_context)
            messages = [Message(role="system", content=system_prompt)] + history
            
            if event_callback:
                await event_callback("assistant_start", content="")

            use_streaming = False
            try:
                supports = self.llm_provider.supports_streaming()
                if isinstance(supports, bool) and supports:
                    use_streaming = True
            except Exception:
                pass

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
                    usage={"total_tokens": len(content.split())}
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
                error_msg = f"RedForge Internal Error: {reason}"
                history.append(Message(role="user", content=f"Refactor your previous response. {reason}"))
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
                    approved=not intent.requires_approval
                )
                
                # Autonomy gate logic
                if intent.requires_approval:
                    if event_callback:
                        await event_callback("confirmation_required", pending_confirmation={"message": content, "tool_calls": []})
                    return {
                        "status": "pending_approval",
                        "response": content,
                        "intent": intent,
                        "session": session,
                        "total_tokens": total_tokens
                    }
                
                # Execute
                if event_callback:
                    await event_callback("tool_start", tool=t.get("tool"), command=t.get("command", "").split() if "command" in t else [])
                
                tool_result = await asyncio.to_thread(self.tool_executor.execute, call)
                
                # Verify
                verified = self.verifier.validate(tool_result, session)
                turn_results.append(verified)
                
                if event_callback:
                    await event_callback("tool_end", 
                                         tool=tool_result.tool_name, 
                                         success=verified.status == VerificationStatus.PASSED,
                                         result=verified)
                
                # Report & Store
                if verified.status == VerificationStatus.PASSED:
                    self.report_engine.add_finding(verified, session_id)
                    # For now, we wrap verified result into MemoryEntry and store
                    from ..contracts.memory import MemoryEntry
                    entry = MemoryEntry(
                        id=str(datetime.now().timestamp()),
                        content=f"Tool {verified.tool_result.tool_name} found: {verified.facts}",
                        metadata={"verified": True}
                    )
                    self.memory_manager.store(session_id, entry)

                history.append(Message(role="user", content=f"Tool Output: {verified.tool_result.stdout}"))
            
            all_results.extend(turn_results)

        return {
            "status": "success",
            "intent": intent,
            "response": history[-1].content,
            "results": all_results,
            "session": session,
            "total_tokens": total_tokens
        }

    # Build prompt logic moved to PlannerService
    pass

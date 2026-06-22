from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import asyncio

from ..session.manager import SessionManager
from ..memory.manager import MemoryManager
from ..skills.loader import DynamicSkillLoader
from ..intent.engine import IntentEngine
from ..tools.executor import ToolExecutor
from ..tools.parser import parse_tool_calls
from ..verifier.verifier import Verifier
from ..verifier.hallucination_guard import HallucinationGuard
from ..report.engine import ReportEngine
from ..safety import SafetyEngine
from ..llm import LLMProvider, Message
from ..contracts.intent import ParsedIntent, IntentType
from ..contracts.tool import ToolCall, ToolResult, VerifiedResult, VerificationStatus
from ..contracts.session import SessionState

logger = logging.getLogger(__name__)

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

    async def process_turn(
        self, 
        raw_input: str, 
        session_id: str,
        mode: Optional[str] = None,
        target: Optional[str] = None,
        autonomy: Optional[str] = None,
        token_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Process a single turn in the pipeline (potentially multiple iterations)."""
        session = self.session_manager.load(session_id)
        if not session:
            # Auto-create the session if it doesn't exist
            m = mode.value if hasattr(mode, "value") else (str(mode) if mode else "bugbounty")
            t = target.value if hasattr(target, "value") else (str(target) if target else None)
            a = autonomy.value if hasattr(autonomy, "value") else (str(autonomy) if autonomy else "manual")
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
        
        for i in range(max_iterations):
            # 4. Dynamic Skill Loader
            skills = self.skill_loader.select_skills(intent.intent_type.value, session.mode, raw_input)
            skill_context = self.skill_loader.build_context(skills, session.mode, intent.intent_type.value)
            
            # Get RAG memory context
            memory_context = self.memory_manager.get_context_for_llm(raw_input)
            
            # 5. LLM Call
            system_prompt = self._build_system_prompt(session, intent, skill_context, memory_context)
            messages = [Message(role="system", content=system_prompt)] + history
            
            if self.llm_provider.supports_streaming():
                content_chunks = []
                async for chunk in self.llm_provider.chat_stream(messages):
                    content_chunks.append(chunk)
                    if token_callback:
                        await token_callback(chunk)
                content = "".join(content_chunks)
                from ..llm.base import ChatResponse
                response = ChatResponse(content=content, model=getattr(self.llm_provider, "model", "fake"))
            else:
                response = await self.llm_provider.chat(messages)
                content = response.content
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
                    tool_name=t.get("tool"),
                    command=t.get("command", "").split() if "command" in t else [],
                    target=session.target or "",
                    timeout_seconds=60,
                    risk_level=intent.risk_level,
                    session_id=session_id,
                    approved=not intent.requires_approval
                )
                
                # Autonomy gate logic
                if intent.requires_approval:
                    return {
                        "status": "pending_approval",
                        "response": content,
                        "intent": intent,
                        "session": session
                    }
                
                # Execute
                tool_result = await asyncio.to_thread(self.tool_executor.execute, call)
                
                # Verify
                verified = self.verifier.validate(tool_result, session)
                turn_results.append(verified)
                
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
            "session": session
        }

    def _build_system_prompt(self, session: SessionState, intent: ParsedIntent, skills: str, memory: str) -> str:
        return f"""You are RedForge, an elite autonomous penetration testing agent.
Active Mode: {session.mode}
Autonomy Level: {session.autonomy}
Target: {session.target or 'NONE'}

## SKILLS & GUIDELINES
{skills}

## DISCOVERED CONTEXT
{memory}

## INSTRUCTIONS
1. Analyze the objective.
2. Maintain target consistency: ONLY interact with {session.target or 'nothing'}.
3. To run a tool, use the format:
TOOL: <name>
COMMAND: <cmd>
4. If you find vulnerabilities, record them as FINDING: blocks.
5. Provide a final summary when the task is done.
"""

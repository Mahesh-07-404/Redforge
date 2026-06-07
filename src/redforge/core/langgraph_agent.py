"""
RedForge LangGraph Agent — Beast Edition
Full think → execute_tool → reflect → save_findings loop
with dynamic skill injection, RAG memory, and real tool execution.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from langgraph.graph import END, StateGraph

from redforge.core.config import Settings, get_settings
from redforge.core.skill_loader import SkillLoader
from redforge.core.state import AgentMode, AgentState, AutonomyLevel, create_initial_state
from redforge.core.tool_executor import ToolExecutor, ToolResult, parse_tool_calls
from redforge.llm.base import Message, ProviderFactory
from redforge.llm.catalog import DEFAULT_MODELS
from redforge.safety import SafetyEngine


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class RedForgeAgent:
    """LangGraph-powered agent for autonomous pentesting"""

    def __init__(
        self,
        config: Optional[Settings] = None,
        llm_provider: str = "gemini",
        model: str = DEFAULT_MODELS["gemini"],
        api_key: str = "",
        base_url: str = "",
        event_handlers: Optional[Dict[str, List[Callable[[Dict[str, Any]], Any]]]] = None,
    ):
        self.config = config or get_settings()
        self.llm = ProviderFactory.create(
            provider=llm_provider,
            model=model,
            api_key=api_key or self.config.llm.api_key,
            base_url=base_url or self.config.llm.base_url,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
        )
        self.skill_loader = SkillLoader()
        self._skills_loaded = False

        self._event_handlers: Dict[str, List[Callable[[Dict[str, Any]], Any]]] = {
            "*": [],
            "run_start": [],
            "run_end": [],
            "assistant_start": [],
            "token": [],
            "assistant_end": [],
            "tool_start": [],
            "tool_end": [],
            "finding": [],
            "confirmation_required": [],
            "error": [],
        }
        if event_handlers:
            for event, callbacks in event_handlers.items():
                for callback in callbacks:
                    self.on(event, callback)

        # Safety engine
        from pathlib import Path
        config_path = Path("config.yaml")
        self.safety = SafetyEngine(config_path if config_path.exists() else None)

        # Tool executor
        self.tool_executor = ToolExecutor(
            safety_engine=self.safety,
            autonomy_level=self.config.autonomy.default_level,
            timeout_default=self.config.tools.timeout if hasattr(self.config.tools, "timeout") else 60,
            event_callback=self._handle_tool_event,
        )

        self.loop_threshold: int = self.config.autonomy.loop_threshold
        self.max_iterations: int = self.config.autonomy.max_iterations

        self._memory_manager = None  # lazily initialised per workspace

        self.graph = self._build_graph()

    def on(self, event: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
        self._event_handlers.setdefault(event, []).append(callback)

    def off(self, event: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
        callbacks = self._event_handlers.get(event, [])
        self._event_handlers[event] = [item for item in callbacks if item is not callback]

    async def _emit(self, event: str, **payload: Any) -> None:
        callbacks = [*self._event_handlers.get(event, []), *self._event_handlers.get("*", [])]
        if not callbacks:
            return

        envelope = {"event": event, **payload}
        for callback in callbacks:
            try:
                result = callback(envelope)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                continue

    async def _handle_tool_event(self, payload: Dict[str, Any]) -> None:
        await self._emit(payload.get("event", "tool_event"), **{k: v for k, v in payload.items() if k != "event"})

    async def _llm_chat_with_events(
        self,
        *,
        node: str,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> tuple[str, int]:
        await self._emit("assistant_start", node=node)

        response_text = ""
        total_tokens = 0
        try:
            if self.config.llm.streaming and getattr(self.llm, "supports_streaming", lambda: False)():
                async for chunk in self.llm.chat_stream(messages=messages, tools=tools):
                    if not chunk:
                        continue
                    response_text += chunk
                    await self._emit("token", node=node, content=chunk)
            else:
                response = await self.llm.chat(messages=messages, tools=tools)
                response_text = response.content if hasattr(response, "content") else str(response)
                total_tokens = (response.usage or {}).get("total_tokens", 0) if hasattr(response, "usage") else 0
                if response_text:
                    await self._emit("token", node=node, content=response_text)
        except Exception:
            # Fall back to non-streaming once if streaming failed partway through.
            if not response_text:
                response = await self.llm.chat(messages=messages, tools=tools)
                response_text = response.content if hasattr(response, "content") else str(response)
                total_tokens = (response.usage or {}).get("total_tokens", 0) if hasattr(response, "usage") else 0
                if response_text:
                    await self._emit("token", node=node, content=response_text)
            else:
                raise

        if not total_tokens:
            total_tokens = max(1, len(response_text.split()))
        await self._emit("assistant_end", node=node, content=response_text, total_tokens=total_tokens)
        return response_text, total_tokens

    # ------------------------------------------------------------------
    # Memory helper
    # ------------------------------------------------------------------

    def _get_memory(self, workspace_id: Optional[str]):
        if not workspace_id:
            return None
        if self._memory_manager and getattr(self._memory_manager, "workspace_id", None) == workspace_id:
            return self._memory_manager
        try:
            from redforge.memory.memory_manager import WorkspaceMemoryManager
            self._memory_manager = WorkspaceMemoryManager(
                workspace_id=workspace_id,
                persist_dir=self.config.memory.persist_dir,
                vector_db=self.config.memory.vector_db,
            )
        except Exception:
            self._memory_manager = None
        return self._memory_manager

    # ------------------------------------------------------------------
    # System Prompt (dynamic)
    # ------------------------------------------------------------------

    def _load_system_prompt(self, state: AgentState) -> str:
        """Build a rich, context-aware system prompt."""
        if not self._skills_loaded:
            self.skill_loader.load_skills()
            self._skills_loaded = True

        mode_val = state.mode.value if isinstance(state.mode, AgentMode) else str(state.mode)
        autonomy_val = (
            state.autonomy_level.value
            if isinstance(state.autonomy_level, AutonomyLevel)
            else str(state.autonomy_level)
        )

        # --- Skill context: top-K relevant to the latest user message ---
        last_user_msg = ""
        for msg in reversed(state.messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        if last_user_msg:
            skill_context = self.skill_loader.get_top_k(last_user_msg, k=6)
        else:
            skill_context = self.skill_loader.get_context_for_mode(mode_val)

        # --- RAG memory context ---
        memory_context = ""
        mem = self._get_memory(state.workspace_id)
        if mem and last_user_msg:
            try:
                memory_context = mem.get_context_for_llm(query=last_user_msg, max_entries=5)
            except Exception:
                pass

        # --- Recent findings summary ---
        findings_summary = ""
        if state.findings:
            recent = state.findings[-5:]
            lines = []
            for f in recent:
                sev = f.get("severity", "?").upper()
                title = f.get("title", f.get("description", "Finding"))
                lines.append(f"  [{sev}] {title}")
            findings_summary = "## RECENT FINDINGS\n" + "\n".join(lines)

        # --- Autonomy rules ---
        autonomy_rules = {
            "manual": (
                "- DESCRIBE each action before asking permission.\n"
                "- Output: TOOL: <name> / COMMAND: <cmd> and wait for [APPROVED] before running any tool.\n"
                "- Never auto-execute."
            ),
            "partial": (
                "- Auto-execute READ-ONLY / passive tools (nmap -sV, whois, dig, curl).\n"
                "- MUST confirm destructive or write actions.\n"
                "- Output TOOL: blocks for all tool calls."
            ),
            "full": (
                "- Execute all tools autonomously.\n"
                "- Still output TOOL: blocks so the user can follow along.\n"
                "- ⚠️  Requires confirmed authorization for target."
            ),
        }.get(autonomy_val, "")

        # --- Tool call syntax ---
        tool_syntax = """
## HOW TO CALL TOOLS
Embed tool calls inline using this exact format (no triple backticks around TOOL:):

TOOL: bash
COMMAND: whoami

TOOL: nmap
TARGET: 192.168.1.1
FLAGS: -sV -T4 --top-ports 100

TOOL: python
CODE:
import socket
print(socket.gethostbyname('example.com'))

TOOL: http_get
URL: https://example.com

TOOL: dns_enum
TARGET: example.com

TOOL: whois
TARGET: example.com

TOOL: ffuf
URL: https://example.com

Available tools: bash, python, nmap, ffuf, http_get, dns_enum, whois, whatweb

After each tool block, I will run it and return OUTPUT: <result>. Then continue reasoning.
"""

        prompt = f"""You are **RedForge**, an elite autonomous penetration testing AI.

## MISSION
Your primary mission is to help with bug bounty, CTF, security learning, and pentesting tasks.
Always verify scope and authorization. Document findings thoroughly.
You are a dual-purpose AI: you can engage in natural, fluid conversation like a human assistant, but you must always be ready to switch to high-intensity pentesting work. Maintain your professional identity at all times.

## AUTONOMY LEVEL: {autonomy_val.upper()}
{autonomy_rules}

## MODE: {mode_val.upper()}
Workspace: {state.workspace_name or 'default'}
Iteration: {state.iteration}/{self.max_iterations}

{tool_syntax}

## RELEVANT SKILLS & KNOWLEDGE
{skill_context if skill_context else 'No specific skills loaded yet.'}

{memory_context if memory_context else ''}

{findings_summary if findings_summary else ''}

## RESPONSE STRUCTURE
1. **Analysis** — What do you know so far?
2. **Plan** — What is the next logical step?
3. **Action** — Issue TOOL: blocks if a tool is needed, or provide the answer.
   - **Request for Work**: In MANUAL mode, before running any tool, you MUST describe exactly what you intend to do and why, then provide the TOOL: block and wait for approval.
4. **Findings** — If you discovered a vulnerability, mark it:
   FINDING: <type> | SEVERITY: <critical/high/medium/low/info> | <description>

## SAFETY (NON-NEGOTIABLE)
- Never attack targets outside the defined scope.
- Stop immediately if instructed.
- Non-destructive methods first.
- All credentials and PII must be redacted from logs.
"""
        return prompt

    def _compute_state_hash(self, state: AgentState) -> str:
        data = {
            "messages_tail": state.messages[-3:] if state.messages else [],
            "iteration": state.iteration,
        }
        return hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()

    # ------------------------------------------------------------------
    # Graph nodes
    # ------------------------------------------------------------------

    async def think_node(self, state: AgentState) -> Dict[str, Any]:
        """Main reasoning node — calls LLM with dynamic prompt."""
        system_prompt = self._load_system_prompt(state)
        messages_for_llm = [Message(role="system", content=system_prompt)]

        # Append conversation history (cap at last 20 to manage context)
        for msg in state.messages[-20:]:
            role = msg.get("role", "user")
            if role == "tool":
                role = "user"
            messages_for_llm.append(
                Message(role=role, content=msg.get("content", ""))
            )

        response_content, used_tokens = await self._llm_chat_with_events(
            node="think",
            messages=messages_for_llm,
        )

        new_message = {
            "role": "assistant",
            "content": response_content,
            "timestamp": datetime.now().isoformat(),
        }

        # Loop detection
        state_hash = self._compute_state_hash(state)
        loop_count = (state.loop_count + 1) if state_hash == state.last_state_hash else 0

        return {
            "messages": state.messages + [new_message],
            "iteration": state.iteration + 1,
            "loop_count": loop_count,
            "last_state_hash": state_hash,
            "pending_confirmation": None,
            "total_tokens": state.total_tokens + used_tokens,
        }

    async def execute_tool_node(self, state: AgentState) -> Dict[str, Any]:
        """Parse tool calls from the last assistant message and execute them."""
        last_msg = state.messages[-1] if state.messages else {}
        response_text = last_msg.get("content", "") if last_msg.get("role") == "assistant" else ""

        if not response_text:
            return {}

        tool_calls = parse_tool_calls(response_text)
        if not tool_calls:
            return {}

        results_text_parts = []
        new_tools_used = list(state.tools_used)

        for call in tool_calls:
            tool_name = call.get("tool", "").lower()
            result: Optional[ToolResult] = None

            try:
                if tool_name == "bash":
                    cmd = call.get("command", "")
                    result = await self.tool_executor.bash(cmd)

                elif tool_name == "python":
                    code = call.get("code", "")
                    result = await self.tool_executor.python_run(code)

                elif tool_name == "nmap":
                    target = call.get("target", "")
                    flags = call.get("flags", "-sV -T4 --top-ports 1000")
                    result = await self.tool_executor.nmap(target, flags)

                elif tool_name == "ffuf":
                    url = call.get("url", "")
                    result = await self.tool_executor.ffuf(url)

                elif tool_name in ("http_get", "http"):
                    url = call.get("url", "")
                    result = await self.tool_executor.http_get(url)

                elif tool_name == "dns_enum":
                    target = call.get("target", "")
                    result = await self.tool_executor.dns_enum(target)

                elif tool_name == "whois":
                    target = call.get("target", "")
                    result = await self.tool_executor.whois(target)

                elif tool_name == "whatweb":
                    url = call.get("url") or call.get("target") or ""
                    result = await self.tool_executor.whatweb(url)

                else:
                    # Unknown tool — run as bash if it looks safe
                    cmd = call.get("command", call.get("args", ""))
                    if cmd:
                        result = await self.tool_executor.bash(str(cmd))

            except Exception as exc:
                result = ToolResult(
                    tool=tool_name,
                    command=str(call),
                    stdout="",
                    stderr="",
                    returncode=-1,
                    duration_s=0.0,
                    error=str(exc),
                )

            if result:
                new_tools_used.append(tool_name)
                status = "✓" if result.success else "✗"
                output_block = (
                    f"\n\n---\nOUTPUT [{status} {tool_name}] ({result.duration_s:.1f}s)\n"
                    f"{result.output}\n---"
                )
                if result.error:
                    output_block += f"\nERROR: {result.error}"
                results_text_parts.append(output_block)

        if not results_text_parts:
            return {}

        tool_output_msg = {
            "role": "tool",
            "content": "".join(results_text_parts),
            "timestamp": datetime.now().isoformat(),
        }

        return {
            "messages": state.messages + [tool_output_msg],
            "tools_used": new_tools_used,
        }

    async def reflect_node(self, state: AgentState) -> Dict[str, Any]:
        """
        After tool execution, ask the LLM to interpret results,
        extract findings, and decide next step.
        """
        last_msgs = state.messages[-3:]  # think + tool_output
        if not any(m.get("role") == "tool" for m in last_msgs):
            return {}  # nothing to reflect on

        system_prompt = self._load_system_prompt(state)
        messages_for_llm = [Message(role="system", content=system_prompt)]

        for msg in state.messages[-20:]:
            role = msg.get("role", "user")
            # LangGraph "tool" role is displayed as user for LLMs that don't support it
            if role == "tool":
                role = "user"
            messages_for_llm.append(Message(role=role, content=msg.get("content", "")))

        messages_for_llm.append(Message(
            role="user",
            content=(
                "Analyse the tool output above.\n"
                "1. What did you find? Any vulnerabilities, open ports, misconfigs, flags?\n"
                "2. Mark discoveries with: FINDING: <type> | SEVERITY: <level> | <description>\n"
                "3. What is the next logical step? Issue another TOOL: block if needed, "
                "or summarise if the task is complete."
            ),
        ))

        response_content, used_tokens = await self._llm_chat_with_events(
            node="reflect",
            messages=messages_for_llm,
        )

        reflect_msg = {
            "role": "assistant",
            "content": response_content,
            "timestamp": datetime.now().isoformat(),
        }

        # Extract inline FINDING: markers
        new_findings = list(state.findings)
        for match in re.finditer(
            r"FINDING:\s*(?P<type>[^|]+)\s*\|\s*SEVERITY:\s*(?P<sev>[^|]+)\s*\|\s*(?P<desc>.+)",
            response_content,
            re.IGNORECASE,
        ):
            finding = {
                "id": f"finding_{len(new_findings)+1}",
                "type": match.group("type").strip(),
                "severity": match.group("sev").strip().lower(),
                "title": match.group("desc").strip()[:120],
                "description": match.group("desc").strip(),
                "timestamp": datetime.now().isoformat(),
            }
            new_findings.append(finding)
            await self._emit("finding", finding=finding)

        return {
            "messages": state.messages + [reflect_msg],
            "findings": new_findings,
            "iteration": state.iteration + 1,
            "total_tokens": state.total_tokens + used_tokens,
        }

    async def save_findings_node(self, state: AgentState) -> Dict[str, Any]:
        """Persist new findings to workspace memory."""
        mem = self._get_memory(state.workspace_id)
        if not mem or not state.findings:
            return {}

        try:
            # Only save findings that don't yet have a persisted flag
            for finding in state.findings:
                if not finding.get("_saved"):
                    mem.add_finding(
                        finding_type=finding.get("type", "general"),
                        title=finding.get("title", "Unknown"),
                        description=finding.get("description", ""),
                        severity=finding.get("severity", "info"),
                    )
                    finding["_saved"] = True
        except Exception:
            pass

        # Also save the conversation exchange
        try:
            user_msgs = [m for m in state.messages if m.get("role") == "user"]
            assist_msgs = [m for m in state.messages if m.get("role") == "assistant"]
            if user_msgs and assist_msgs:
                mem.add_session(
                    user_input=user_msgs[-1].get("content", "")[:500],
                    response=assist_msgs[-1].get("content", "")[:1000],
                )
        except Exception:
            pass

        return {"findings": state.findings}

    async def await_confirmation_node(self, state: AgentState) -> Dict[str, Any]:
        """Signal that user confirmation is needed (handled by the CLI loop)."""
        pending = {
            "type": "user_input",
            "message": state.messages[-1].get("content", "") if state.messages else "",
            "tool_calls": parse_tool_calls(state.messages[-1].get("content", "")) if state.messages else [],
        }
        await self._emit("confirmation_required", pending_confirmation=pending)
        return {"pending_confirmation": pending}

    async def handle_error_node(self, state: AgentState) -> Dict[str, Any]:
        await self._emit("error", message=state.error or "Unknown error")
        return {"error": state.error or "Unknown error", "iteration": state.iteration}

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def _route_after_think(self, state: AgentState) -> str:
        """Decide what to do after thinking."""
        # Hard stop conditions
        if state.iteration >= self.max_iterations:
            return "save_findings"
        if state.loop_count >= self.loop_threshold:
            return "save_findings"

        last_msg = state.messages[-1] if state.messages else {}
        content = last_msg.get("content", "") if last_msg.get("role") == "assistant" else ""

        # If there are TOOL: blocks, execute them
        from redforge.core.tool_executor import parse_tool_calls
        calls = parse_tool_calls(content)
        if calls:
            autonomy = (
                state.autonomy_level.value
                if isinstance(state.autonomy_level, AutonomyLevel)
                else str(state.autonomy_level)
            )
            if autonomy == "manual":
                return "await_confirmation"
            
            if autonomy == "partial":
                from redforge.core.autonomy_controller import AutonomyController
                ac = AutonomyController()
                for call in calls:
                    tool = call.get("tool", "")
                    # If any tool is not definitely safe, ask for confirmation
                    if ac.assess_action_risk(tool).value not in ("safe", "low"):
                        return "await_confirmation"
            
            return "execute_tool"

        return "save_findings"

    def _route_after_execute(self, state: AgentState) -> str:
        """After tool execution, always reflect."""
        last_msgs = state.messages[-3:]
        if any(m.get("role") == "tool" for m in last_msgs):
            return "reflect"
        return "save_findings"

    def _route_after_reflect(self, state: AgentState) -> str:
        """After reflection, check if more tool calls are needed."""
        if state.iteration >= self.max_iterations:
            return "save_findings"
        if state.loop_count >= self.loop_threshold:
            return "save_findings"

        last_msg = state.messages[-1] if state.messages else {}
        content = last_msg.get("content", "") if last_msg.get("role") == "assistant" else ""
        calls = parse_tool_calls(content)
        if calls:
            autonomy = (
                state.autonomy_level.value
                if isinstance(state.autonomy_level, AutonomyLevel)
                else str(state.autonomy_level)
            )
            if autonomy == "manual":
                return "await_confirmation"
            
            if autonomy == "partial":
                from redforge.core.autonomy_controller import AutonomyController
                ac = AutonomyController()
                for call in calls:
                    tool = call.get("tool", "")
                    # If any tool is not definitely safe, ask for confirmation
                    if ac.assess_action_risk(tool).value not in ("safe", "low"):
                        return "await_confirmation"
            
            return "execute_tool"

        return "save_findings"

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self) -> Any:
        graph = StateGraph(AgentState)

        graph.add_node("think", self.think_node)
        graph.add_node("execute_tool", self.execute_tool_node)
        graph.add_node("reflect", self.reflect_node)
        graph.add_node("save_findings", self.save_findings_node)
        graph.add_node("await_confirmation", self.await_confirmation_node)
        graph.add_node("handle_error", self.handle_error_node)

        graph.set_entry_point("think")

        graph.add_conditional_edges(
            "think",
            self._route_after_think,
            {
                "execute_tool": "execute_tool",
                "await_confirmation": "await_confirmation",
                "save_findings": "save_findings",
            },
        )
        graph.add_conditional_edges(
            "execute_tool",
            self._route_after_execute,
            {"reflect": "reflect", "save_findings": "save_findings"},
        )
        graph.add_conditional_edges(
            "reflect",
            self._route_after_reflect,
            {
                "execute_tool": "execute_tool",
                "await_confirmation": "await_confirmation",
                "save_findings": "save_findings",
            },
        )
        graph.add_edge("save_findings", END)
        graph.add_edge("await_confirmation", END)   # CLI will re-invoke after approval
        graph.add_edge("handle_error", END)

        return graph.compile()

    def _merge_state(self, state: AgentState, updates: Dict[str, Any]) -> AgentState:
        if not updates:
            return state
        merged = state.model_dump()
        merged.update(updates)
        return AgentState(**merged)

    # ------------------------------------------------------------------
    # Public run method
    # ------------------------------------------------------------------

    async def run(
        self,
        user_input: str,
        workspace_id: Optional[str] = None,
        workspace_name: Optional[str] = None,
        autonomy_level: AutonomyLevel = AutonomyLevel.MANUAL,
        mode: AgentMode = AgentMode.GOAL_BASED,
        prior_state: Optional[AgentState] = None,
    ) -> AgentState:
        """Run the agent with user input, optionally continuing from prior state."""
        await self._emit(
            "run_start",
            user_input=user_input,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
        )
        if prior_state:
            # Continue from existing state — append the new user message
            new_msg = {
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat(),
            }
            import copy
            state_dict = prior_state.model_dump()
            state_dict["messages"] = prior_state.messages + [new_msg]
            state_dict["pending_confirmation"] = None
            state_dict["autonomy_level"] = autonomy_level
            state_dict["mode"] = mode
            initial_state = AgentState(**state_dict)
        else:
            initial_state = create_initial_state(
                user_input=user_input,
                workspace_id=workspace_id,
                workspace_name=workspace_name,
                autonomy_level=autonomy_level,
                mode=mode,
            )

        result = initial_state
        try:
            result = self._merge_state(result, await self.think_node(result))
            next_step = self._route_after_think(result)

            while True:
                if next_step == "await_confirmation":
                    result = self._merge_state(result, await self.await_confirmation_node(result))
                    break

                if next_step == "save_findings":
                    result = self._merge_state(result, await self.save_findings_node(result))
                    break

                if next_step == "execute_tool":
                    result = self._merge_state(result, await self.execute_tool_node(result))
                    next_step = self._route_after_execute(result)
                    continue

                if next_step == "reflect":
                    result = self._merge_state(result, await self.reflect_node(result))
                    next_step = self._route_after_reflect(result)
                    continue

                result = self._merge_state(result, await self.handle_error_node(result))
                break
        except Exception as exc:
            error_state = result.model_dump()
            error_state["error"] = str(exc)
            result = AgentState(**error_state)
            result = self._merge_state(result, await self.handle_error_node(result))
        await self._emit(
            "run_end",
            iteration=result.iteration,
            total_tokens=result.total_tokens,
            pending_confirmation=result.pending_confirmation,
            findings=result.findings,
        )
        return result

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        stats = self.skill_loader.stats()
        return {
            "llm_provider": getattr(self.llm, "model", "unknown"),
            "skills_loaded": self._skills_loaded,
            "skills_total": stats.get("total", 0),
            "skills_by_category": stats.get("by_category", {}),
            "skills_dir": stats.get("skills_dir", ""),
            "loop_threshold": self.loop_threshold,
            "max_iterations": self.max_iterations,
            "tool_history": len(self.tool_executor.get_history()),
        }

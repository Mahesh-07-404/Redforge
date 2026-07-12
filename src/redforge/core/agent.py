import logging
from collections.abc import Callable
from typing import Any

from .pipeline import Pipeline
from .state import AgentState

logger = logging.getLogger(__name__)


class RedForgeAgent:
    """
    Orchestrates the RedForge pipeline.
    Matches the Phase 2 Architecture: no business logic, just orchestration.
    """

    def __init__(self, pipeline: Pipeline | None = None, **kwargs):
        self._event_handlers: dict[str, list[Callable[[dict[str, Any]], Any]]] = {
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
        self.max_iterations = 10
        self.loop_threshold = 3

        if pipeline is not None:
            self.pipeline = pipeline
        else:
            config = kwargs.get("config")
            llm_provider = kwargs.get("llm_provider")
            model = kwargs.get("model")
            api_key = kwargs.get("api_key")
            base_url = kwargs.get("base_url")

            from ..config.config import get_settings
            from ..memory.manager import MemoryManager
            from ..providers import get_llm
            from ..reports.engine import ReportEngine
            from ..skills.loader import DynamicSkillLoader
            from ..skills.registry import SkillRegistry
            from ..tools.manager import ToolService as ToolExecutor
            from .intent import IntentService as IntentEngine
            from .intent import TargetWatcher
            from .safety import SafetyEngine
            from .session import (
                EventBus,
                SessionManager,
                SessionStore,
                TargetStateMachine,
            )
            from .verifier import Verifier

            settings = config or get_settings()

            from pathlib import Path

            persist_path = Path(settings.memory.persist_dir)
            persist_path.mkdir(parents=True, exist_ok=True)
            db_path = str(persist_path / "sessions.db")
            store = SessionStore(db_path)
            session_manager = SessionManager(store)

            memory_manager = MemoryManager(settings.memory.persist_dir)

            target_state = TargetStateMachine()
            event_bus = EventBus()
            target_watcher = TargetWatcher(target_state, event_bus)
            intent_engine = IntentEngine(target_watcher)

            skill_registry = SkillRegistry()
            skill_loader = DynamicSkillLoader(skill_registry)

            tool_executor = ToolExecutor()
            verifier = Verifier()

            report_engine = ReportEngine()

            safety_engine = SafetyEngine()

            provider = llm_provider or settings.llm.provider
            model_name = model or settings.llm.model
            key = api_key or settings.llm.api_key
            url = base_url or settings.llm.base_url

            llm = get_llm(provider=provider, model=model_name, api_key=key, base_url=url)

            self.pipeline = Pipeline(
                session_manager=session_manager,
                memory_manager=memory_manager,
                skill_loader=skill_loader,
                intent_engine=intent_engine,
                tool_executor=tool_executor,
                verifier=verifier,
                report_engine=report_engine,
                safety_engine=safety_engine,
                llm_provider=llm,
            )

    def on(self, event: str, callback: Callable[[dict[str, Any]], Any]) -> None:
        self._event_handlers.setdefault(event, []).append(callback)

    def off(self, event: str, callback: Callable[[dict[str, Any]], Any]) -> None:
        callbacks = self._event_handlers.get(event, [])
        self._event_handlers[event] = [item for item in callbacks if item is not callback]

    async def _emit(self, event: str, **payload: Any) -> None:
        callbacks = [*self._event_handlers.get(event, []), *self._event_handlers.get("*", [])]
        for callback in callbacks:
            try:
                import inspect

                result = callback({"event": event, **payload})
                if inspect.isawaitable(result):
                    await result
            except Exception as e:
                logger.error(f"Error in event handler for {event}: {e}")

    async def run(self, user_input: str, session_id: str | None = None, **kwargs) -> AgentState:
        """
        Runs a single turn of the pipeline and emits events.
        Compatible with legacy signatures by accepting **kwargs.
        """
        sid = session_id or "default"
        await self._emit("run_start", user_input=user_input, session_id=sid)

        state_dict: dict[str, Any] = {
            "messages": [],
            "findings": [],
            "tools_used": [],
            "total_tokens": 0,
            "error": None,
            "pending_confirmation": None,
        }

        async def token_cb(token: str):
            await self._emit("token", token=token)

        async def event_cb(event: str, **payload: Any):
            await self._emit(event, **payload)
            if event == "assistant_end":
                content = payload.get("content", "")
                state_dict["messages"].append({"role": "assistant", "content": content})
            elif event == "token":
                pass
            elif event == "tool_start":
                tool_name = payload.get("tool")
                if tool_name not in state_dict["tools_used"]:
                    state_dict["tools_used"].append(tool_name)
            elif event == "tool_end":
                res = payload.get("result")
                stdout = ""
                error = None
                if res:
                    if hasattr(res, "tool_result"):
                        stdout = res.tool_result.stdout or ""
                        error = res.tool_result.error
                    elif isinstance(res, dict):
                        tr = res.get("tool_result", {})
                        stdout = tr.get("stdout") or ""
                        error = tr.get("error")
                state_dict["messages"].append({"role": "tool", "content": stdout or error or ""})
            elif event == "finding":
                state_dict["findings"].append(payload.get("finding"))
            elif event == "confirmation_required":
                state_dict["pending_confirmation"] = payload.get("pending_confirmation")

        mode = kwargs.get("mode")
        target = kwargs.get("target")
        autonomy = kwargs.get("autonomy_level") or kwargs.get("autonomy")
        try:
            result = await self.pipeline.process_turn(
                user_input,
                sid,
                mode=mode,
                target=target,
                autonomy=autonomy,
                token_callback=token_cb,
                event_callback=event_cb,
            )

            state_dict["total_tokens"] = result.get("total_tokens", 0)

            await self._emit("run_end", status=result.get("status"))

        except Exception as e:
            await self._emit("error", message=str(e))
            logger.exception(f"Pipeline execution failed: {e}")
            state_dict["error"] = str(e)

        return AgentState(**state_dict)

    @property
    def llm(self):
        return self.pipeline.llm_provider

    @llm.setter
    def llm(self, value):
        self.pipeline.llm_provider = value

    @property
    def skill_loader(self):
        from .skill_loader import SkillLoader

        loader = SkillLoader()
        loader.registry = self.pipeline.skill_loader.registry
        loader.loader = self.pipeline.skill_loader
        loader._loaded = True
        return loader

    @property
    def tool_executor(self):
        if not hasattr(self, "_legacy_tool_executor"):
            from .tool_executor import ToolExecutor as LegacyToolExecutor

            self._legacy_tool_executor = LegacyToolExecutor(
                safety_engine=self.pipeline.safety_engine, autonomy_level="manual"
            )
        return self._legacy_tool_executor

    def get_status(self) -> dict[str, Any]:
        return {
            "llm_provider": getattr(self.pipeline.llm_provider, "model", "unknown"),
            "skills_total": len(self.pipeline.skill_loader.registry.skills),
            "tool_history": len(getattr(self.tool_executor, "_history", [])),
        }

    async def _classify_intent(self, text: str) -> str:
        lower = text.lower()
        if any(greet in lower for greet in ["yo", "hello", "hi", "hey", "thanks", "thank you"]):
            return "CHAT"

        if hasattr(self, "llm") and self.llm:
            try:
                from ..providers import Message

                resp = await self.llm.chat([Message(role="user", content=text)])
                if isinstance(resp, str):
                    return resp
                return getattr(resp, "content", "SCAN")
            except (
                Exception
            ) as exc:  # nosec B110 - intent classification failure falls back to SCAN
                logger.debug("Intent classification failed, falling back to SCAN: %s", exc)
        return "SCAN"

    def _merge_state(self, state: AgentState, update: dict) -> AgentState:
        if "target" in update and state.target and update["target"] != state.target:
            raise ValueError("Target immutability violation")
        state_dict = state.model_dump()
        state_dict.update(update)
        return AgentState(**state_dict)

    async def verify_node(self, state: AgentState) -> dict:
        response_text, tokens = await self._generate_validated_response(state)

        findings = []
        for line in response_text.splitlines():
            line = line.strip()
            if line.upper().startswith("FINDING:"):
                parts = [p.strip() for p in line[8:].split("|")]
                if len(parts) >= 3:
                    finding_type = parts[0]
                    severity = parts[1].replace("SEVERITY:", "").strip().lower()
                    desc = parts[2]

                    tool_found = None
                    command_found = None
                    evidence = None
                    status = "UNVERIFIED"

                    history = getattr(self.tool_executor, "_history", [])
                    if history:
                        last_result = history[-1]
                        tool_found = last_result.tool
                        command_found = last_result.command
                        evidence = {"stdout": last_result.stdout}
                        status = "VERIFIED"

                    findings.append(
                        {
                            "id": "mock-finding-id",
                            "type": finding_type,
                            "severity": severity,
                            "title": f"Vulnerability Finding: {finding_type}",
                            "description": desc,
                            "target": state.target,
                            "tool": tool_found,
                            "command": command_found,
                            "status": status,
                            "evidence": evidence,
                        }
                    )
        state_dict = state.model_dump()
        state_dict["findings"] = findings
        return state_dict

    async def _generate_validated_response(self, state: AgentState) -> tuple[str, int]:
        return "", 0

from typing import Dict, Any, List, Optional, Callable
import logging

from .pipeline import Pipeline
from ..contracts.session import SessionState
from .state import AgentState, WorkflowPhase

logger = logging.getLogger(__name__)

class RedForgeAgent:
    """
    Orchestrates the RedForge pipeline.
    Matches the Phase 2 Architecture: no business logic, just orchestration.
    """
    def __init__(self, pipeline: Optional[Pipeline] = None, **kwargs):
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
            
            from .config import get_settings
            from ..session.store import SessionStore
            from ..session.manager import SessionManager
            from ..memory.manager import MemoryManager
            from ..session.target import TargetStateMachine
            from ..session.events import EventBus
            from ..intent.target_watcher import TargetWatcher
            from ..intent.engine import IntentEngine
            from ..skills.registry import SkillRegistry
            from ..skills.loader import DynamicSkillLoader
            from ..tools.executor import ToolExecutor
            from ..verifier.verifier import Verifier
            from ..report.engine import ReportEngine
            from ..safety import SafetyEngine
            from ..llm import get_llm
            
            settings = config or get_settings()
            
            store = SessionStore()
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
            
            llm = get_llm(
                provider=provider,
                model=model_name,
                api_key=key,
                base_url=url
            )
            
            self.pipeline = Pipeline(
                session_manager=session_manager,
                memory_manager=memory_manager,
                skill_loader=skill_loader,
                intent_engine=intent_engine,
                tool_executor=tool_executor,
                verifier=verifier,
                report_engine=report_engine,
                safety_engine=safety_engine,
                llm_provider=llm
            )

    def on(self, event: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
        self._event_handlers.setdefault(event, []).append(callback)

    def off(self, event: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
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

    async def run(
        self, 
        user_input: str, 
        session_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        **kwargs
    ) -> AgentState:
        """
        Runs a single turn of the pipeline and emits events.
        Compatible with legacy signatures by accepting **kwargs.
        """
        sid = session_id or workspace_id or "default"
        await self._emit("run_start", user_input=user_input, session_id=sid)
        
        state_dict = {
            "messages": [],
            "findings": [],
            "tools_used": [],
            "total_tokens": 0,
            "error": None,
            "pending_confirmation": None
        }

        try:
            result = await self.pipeline.process_turn(user_input, sid)
            
            # Populate state_dict from pipeline result for UI compatibility
            if "response" in result:
                await self._emit("assistant_end", content=result["response"])
                state_dict["messages"].append({"role": "assistant", "content": result["response"]})
            
            if "results" in result:
                for res in result["results"]:
                    if hasattr(res, "tool_result"):
                        tool_res = res.tool_result
                        state_dict["tools_used"].append(tool_res.tool_name)
                        state_dict["messages"].append({"role": "tool", "content": tool_res.stdout or tool_res.error})
                        await self._emit("tool_end", 
                                         tool=tool_res.tool_name, 
                                         success=res.status.value == "passed",
                                         result=tool_res.to_dict() if hasattr(tool_res, "to_dict") else tool_res)

            if result.get("status") == "pending_approval":
                state_dict["pending_confirmation"] = {"message": result.get("response"), "tool_calls": []}
                await self._emit("confirmation_required", 
                                 pending_confirmation=state_dict["pending_confirmation"])

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
                safety_engine=self.pipeline.safety_engine,
                autonomy_level="manual"
            )
        return self._legacy_tool_executor

    def get_status(self) -> Dict[str, Any]:
        return {
            "llm_provider": getattr(self.pipeline.llm_provider, "model", "unknown"),
            "skills_total": len(self.pipeline.skill_loader.registry.skills),
            "tool_history": len(getattr(self.tool_executor, "_history", []))
        }

    async def _classify_intent(self, text: str) -> str:
        lower = text.lower()
        if any(greet in lower for greet in ["yo", "hello", "hi", "hey", "thanks", "thank you"]):
            return "CHAT"
        
        if hasattr(self, "llm") and self.llm:
            try:
                from ..llm import Message
                resp = await self.llm.chat([Message(role="user", content=text)])
                if isinstance(resp, str):
                    return resp
                return getattr(resp, "content", "SCAN")
            except Exception:
                pass
        return "SCAN"

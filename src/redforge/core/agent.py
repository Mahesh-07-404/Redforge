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
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
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

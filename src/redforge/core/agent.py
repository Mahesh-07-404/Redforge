from typing import Dict, Any, List, Optional, Callable
import logging

from .pipeline import Pipeline
from ..contracts.session import SessionState

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

    async def run(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """Runs a single turn of the pipeline and emits events."""
        await self._emit("run_start", user_input=user_input, session_id=session_id)
        
        try:
            result = await self.pipeline.process_turn(user_input, session_id)
            
            # Emit results as events for the UI
            if "response" in result:
                await self._emit("assistant_end", content=result["response"])
            
            if "results" in result:
                for res in result["results"]:
                    if hasattr(res, "tool_result"):
                        await self._emit("tool_end", tool=res.tool_result.tool_name, success=res.status.value == "passed")

            await self._emit("run_end", status=result.get("status"))
            return result
        except Exception as e:
            await self._emit("error", message=str(e))
            logger.exception(f"Pipeline execution failed: {e}")
            return {"status": "error", "message": str(e)}

    @property
    def llm(self):
        return self.pipeline.llm_provider

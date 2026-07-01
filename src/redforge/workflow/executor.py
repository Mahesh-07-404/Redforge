import asyncio
from typing import Any

from .contracts import WorkflowStage


class StageExecutor:
    async def execute_stage(self, stage: WorkflowStage, context: dict[str, Any]) -> str:
        await asyncio.sleep(0.01)
        return f"Stage {stage.id} completed successfully."

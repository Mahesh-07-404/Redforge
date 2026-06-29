import time
from typing import List, Optional, Callable
from .contracts import ApprovedPlan, ExecutionResult, TaskResult
from .scheduler import TaskScheduler
from .stream import StreamManager
from .events import ExecutionEvent
from .state import ExecutionStatus
from ..policy.policy_decision import DecisionStatus

class Executor:
    def __init__(self, stream_manager: Optional[StreamManager] = None):
        self.stream_manager = stream_manager or StreamManager()
        self.scheduler = TaskScheduler(self.stream_manager)

    async def execute(self, approved_plan: ApprovedPlan) -> ExecutionResult:
        if approved_plan.decision.status != DecisionStatus.ALLOW:
            raise ValueError(f"Cannot execute plan: Policy status is {approved_plan.decision.status.value}")
            
        start_time = time.time()
        
        self.stream_manager.emit(ExecutionEvent(event_type="ExecutionStarted", data={"goal": approved_plan.plan.goal}))
        
        task_results = await self.scheduler.execute_plan_tasks(approved_plan.plan.ordered_tasks)
        
        status = ExecutionStatus.COMPLETED
        for r in task_results:
            if r.status in (ExecutionStatus.FAILED, ExecutionStatus.TIMED_OUT):
                status = ExecutionStatus.FAILED
                break
            elif r.status == ExecutionStatus.CANCELLED:
                status = ExecutionStatus.CANCELLED
                
        duration = time.time() - start_time
        
        self.stream_manager.emit(ExecutionEvent(
            event_type="ExecutionFinished",
            data={"status": status.value, "duration": duration}
        ))
        
        return ExecutionResult(
            plan_goal=approved_plan.plan.goal,
            status=status,
            task_results=task_results,
            duration=duration
        )

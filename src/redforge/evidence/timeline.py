from datetime import datetime

from ..executor.contracts import ExecutionResult
from .contracts import ExecutionTimeline, TimelineEvent


class TimelineGenerator:
    @staticmethod
    def generate_timeline(
        session_id: str, execution_id: str, exec_result: ExecutionResult
    ) -> ExecutionTimeline:
        events = []
        start_time = datetime.now().isoformat()
        events.append(
            TimelineEvent(
                timestamp=start_time,
                event="ExecutionStarted",
                description=f"Execution started for goal: {exec_result.plan_goal}",
            )
        )

        for task_res in exec_result.task_results:
            events.append(
                TimelineEvent(
                    timestamp=start_time,
                    event="TaskStarted",
                    description=f"Task {task_res.task_id} execution started",
                )
            )
            events.append(
                TimelineEvent(
                    timestamp=datetime.now().isoformat(),
                    event="TaskFinished",
                    description=f"Task {task_res.task_id} finished with status {task_res.status.value}",
                )
            )

        events.append(
            TimelineEvent(
                timestamp=datetime.now().isoformat(),
                event="ExecutionFinished",
                description=f"Execution finished with status {exec_result.status.value}",
            )
        )

        return ExecutionTimeline(session_id=session_id, execution_id=execution_id, events=events)

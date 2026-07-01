from ..planner.task import Task
from ..planner.task_graph import TaskGraph
from .contracts import TaskResult
from .runner import Runner
from .state import ExecutionStatus


class TaskScheduler:
    def __init__(self, stream_manager=None):
        self.stream_manager = stream_manager
        self.cancelled = False
        self.runner = Runner()

    def cancel(self):
        self.cancelled = True

    async def execute_plan_tasks(
        self, tasks: list[Task], timeout_per_task: float = 60.0, retries_per_task: int = 1
    ) -> list[TaskResult]:
        graph = TaskGraph()
        for t in tasks:
            graph.add_task(t)

        try:
            ordered_tasks = graph.get_ordered_tasks()
        except Exception:
            ordered_tasks = tasks

        results = []
        from .events import ExecutionEvent

        for task in ordered_tasks:
            if self.cancelled:
                res = TaskResult(
                    task_id=task.id,
                    status=ExecutionStatus.CANCELLED,
                    error="Execution cancelled by scheduler.",
                )
                results.append(res)
                if self.stream_manager:
                    self.stream_manager.emit(
                        ExecutionEvent(
                            event_type="TaskFailed", task_id=task.id, data={"error": res.error}
                        )
                    )
                continue

            dep_failed = False
            for dep in task.dependencies:
                dep_res = next((r for r in results if r.task_id == dep), None)
                if dep_res and dep_res.status in (
                    ExecutionStatus.FAILED,
                    ExecutionStatus.TIMED_OUT,
                    ExecutionStatus.CANCELLED,
                ):
                    dep_failed = True
                    break

            if dep_failed:
                res = TaskResult(
                    task_id=task.id, status=ExecutionStatus.SKIPPED, error="Dependency failed."
                )
                results.append(res)
                if self.stream_manager:
                    self.stream_manager.emit(
                        ExecutionEvent(
                            event_type="TaskFailed", task_id=task.id, data={"error": res.error}
                        )
                    )
                continue

            if self.stream_manager:
                self.stream_manager.emit(ExecutionEvent(event_type="TaskStarted", task_id=task.id))

            try:
                res = await self.runner.execute_task(
                    task, timeout=timeout_per_task, retries=retries_per_task
                )
            except Exception as e:
                res = TaskResult(task_id=task.id, status=ExecutionStatus.FAILED, error=str(e))

            results.append(res)

            if self.stream_manager:
                event_type = (
                    "TaskFinished" if res.status == ExecutionStatus.COMPLETED else "TaskFailed"
                )
                self.stream_manager.emit(
                    ExecutionEvent(
                        event_type=event_type,
                        task_id=task.id,
                        data={"status": res.status.value, "error": res.error},
                    )
                )

        return results

import time
from .contracts import TaskResult
from .state import ExecutionStatus
from .process import ProcessManager
from .parser import OutputParser
from ..planner.task import Task

class Runner:
    async def execute_task(self, task: Task, timeout: float = 60.0, retries: int = 1) -> TaskResult:
        binary = task.tool_hint or "echo"
        command = [binary]
        if binary == "echo":
            command.append(f"Running task {task.title}")
            
        start_time = time.time()
        status = ExecutionStatus.COMPLETED
        stdout, stderr, exit_code = "", "", 0
        error_msg = None
        
        for attempt in range(retries):
            pm = ProcessManager(command)
            try:
                pm.spawn()
                stdout, stderr, exit_code = pm.wait(timeout=timeout)
                if exit_code == 0:
                    status = ExecutionStatus.COMPLETED
                    error_msg = None
                    break
                else:
                    status = ExecutionStatus.FAILED
                    error_msg = f"Process exited with code {exit_code}. Stderr: {stderr}"
            except TimeoutError:
                status = ExecutionStatus.TIMED_OUT
                error_msg = "Task execution timed out."
            except Exception as e:
                status = ExecutionStatus.FAILED
                error_msg = f"Failed to launch process: {str(e)}"
                
        duration = time.time() - start_time
        structured = OutputParser.parse(binary, stdout)
        
        return TaskResult(
            task_id=task.id,
            status=status,
            raw_output=stdout,
            structured_output=structured,
            exit_code=exit_code,
            duration=duration,
            error=error_msg
        )

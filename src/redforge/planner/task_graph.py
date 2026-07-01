from .task import Task


class TaskGraph:
    def __init__(self):
        self.tasks: dict[str, Task] = {}

    def add_task(self, task: Task):
        self.tasks[task.id] = task

    def get_ordered_tasks(self) -> list[Task]:
        # Topological sort
        visited: set[str] = set()
        temp: set[str] = set()
        order: list[str] = []

        def visit(node: str):
            if node in temp:
                raise ValueError(f"Cycle detected in task graph at node '{node}'")
            if node not in visited:
                temp.add(node)
                task = self.tasks.get(node)
                if task:
                    for dep in task.dependencies:
                        visit(dep)
                temp.remove(node)
                visited.add(node)
                order.append(node)

        for task_id in self.tasks:
            visit(task_id)

        return [self.tasks[tid] for tid in order]

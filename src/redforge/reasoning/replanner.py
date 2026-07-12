from ..planner.task import Task
from .world_state import WorldState


class Replanner:
    @staticmethod
    def replan(current_tasks: list[Task], world_state: WorldState) -> list[Task]:
        new_tasks = []
        for t in current_tasks:
            if t.id == "subfinder" and not world_state.hosts:
                new_tasks.append(
                    Task(
                        id="amass",
                        title="Amass Recon",
                        description="Amass scan fallback",
                        tool_hint="amass",
                    )
                )
            else:
                new_tasks.append(t)
        return new_tasks

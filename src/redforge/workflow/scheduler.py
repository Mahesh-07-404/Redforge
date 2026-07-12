from .contracts import WorkflowStage


class WorkflowScheduler:
    @staticmethod
    def schedule_stages(stages: list[WorkflowStage]) -> list[WorkflowStage]:
        sorted_stages = []
        visited = set()

        def visit(stage):
            if stage.id in visited:
                return
            for dep_id in stage.dependencies:
                dep_stage = next((s for s in stages if s.id == dep_id), None)
                if dep_stage:
                    visit(dep_stage)
            visited.add(stage.id)
            sorted_stages.append(stage)

        for stage in stages:
            visit(stage)
        return sorted_stages

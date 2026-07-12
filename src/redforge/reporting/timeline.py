class ReportTimelineGenerator:
    @staticmethod
    def generate_timeline(steps: list[str]) -> list[str]:
        timeline = []
        for step in steps:
            timeline.append(f"Milestone: {step}")
        return timeline

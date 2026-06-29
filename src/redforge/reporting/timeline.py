from typing import List

class ReportTimelineGenerator:
    @staticmethod
    def generate_timeline(steps: List[str]) -> List[str]:
        timeline = []
        for step in steps:
            timeline.append(f"Milestone: {step}")
        return timeline

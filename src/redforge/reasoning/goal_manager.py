import uuid
from datetime import datetime

from .contracts import Goal


class GoalManager:
    def __init__(self):
        self.goals: dict[str, Goal] = {}

    def create_goal(self, text: str) -> Goal:
        gid = str(uuid.uuid4())
        g = Goal(id=gid, text=text, status="pending", created_at=datetime.now().isoformat())
        self.goals[gid] = g
        return g

    def update_goal_status(self, goal_id: str, status: str):
        if goal_id in self.goals:
            self.goals[goal_id].status = status

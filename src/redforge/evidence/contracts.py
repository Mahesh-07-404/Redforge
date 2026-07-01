from pydantic import BaseModel

from .metadata import ArtifactMetadata


class Artifact(BaseModel):
    id: str
    name: str
    content_type: str
    content: str
    metadata: ArtifactMetadata


class TimelineEvent(BaseModel):
    timestamp: str
    event: str
    description: str


class ExecutionTimeline(BaseModel):
    session_id: str
    execution_id: str
    events: list[TimelineEvent] = []


class Evidence(BaseModel):
    id: str
    task_id: str
    status: str
    duration: float
    exit_code: int
    artifacts: list[Artifact] = []


class EvidenceBundle(BaseModel):
    session_id: str
    execution_id: str
    plan_goal: str
    timeline: ExecutionTimeline
    evidence_list: list[Evidence] = []

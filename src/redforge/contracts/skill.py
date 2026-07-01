from pydantic import BaseModel


class SkillRecord(BaseModel):
    id: str
    path: str
    title: str
    summary: str
    tags: list[str]
    mode: list[str]
    embedding_id: str | None


class SkillQuery(BaseModel):
    intent: str
    mode: str
    k: int = 5


class SkillBundle(BaseModel):
    skills: list[str]
    total_tokens: int

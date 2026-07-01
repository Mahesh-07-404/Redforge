from pydantic import BaseModel

from .schema import NormalizedEntity


class EntityRelation(BaseModel):
    source_id: str
    target_id: str
    relation_type: str


class NormalizedBundle(BaseModel):
    session_id: str
    execution_id: str
    entities: list[NormalizedEntity] = []
    relationships: list[EntityRelation] = []


class NormalizationStatus(BaseModel):
    status: str
    errors: list[str] = []
    warnings: list[str] = []


class NormalizationResult(BaseModel):
    bundle: NormalizedBundle
    status: NormalizationStatus

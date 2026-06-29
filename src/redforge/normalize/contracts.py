from typing import List
from pydantic import BaseModel
from .schema import NormalizedEntity

class EntityRelation(BaseModel):
    source_id: str
    target_id: str
    relation_type: str

class NormalizedBundle(BaseModel):
    session_id: str
    execution_id: str
    entities: List[NormalizedEntity] = []
    relationships: List[EntityRelation] = []

class NormalizationStatus(BaseModel):
    status: str
    errors: List[str] = []
    warnings: List[str] = []

class NormalizationResult(BaseModel):
    bundle: NormalizedBundle
    status: NormalizationStatus

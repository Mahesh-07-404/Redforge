from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class EvidenceReference(BaseModel):
    task_id: str
    artifact_id: str
    hash: str

class NormalizedEntity(BaseModel):
    id: str
    entity_type: str
    value: str
    source_tool: str
    confidence: float = 1.0
    session_id: str
    execution_id: str
    target: str
    timestamp: str
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    evidence_reference: Optional[EvidenceReference] = None

from typing import Any

from pydantic import BaseModel


class Chunk(BaseModel):
    id: str
    session_id: str
    source: str
    content: str
    metadata: dict[str, Any] = {}
    tags: list[str] = []
    hash: str
    timestamp: str


class RAGQuery(BaseModel):
    query_text: str
    session_id: str
    limit: int = 5
    metadata_filter: dict[str, Any] = {}


class RAGResult(BaseModel):
    chunk: Chunk
    score: float
    source_type: str


class RAGContext(BaseModel):
    context_text: str
    sources: list[RAGResult]
    token_count: int

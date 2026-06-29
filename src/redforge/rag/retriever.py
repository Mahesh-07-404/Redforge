from typing import List
from .contracts import Chunk, RAGQuery, RAGResult
from .engine import RAGEngine

class Retriever:
    def __init__(self, engine: RAGEngine):
        self.engine = engine

    async def retrieve(self, query_text: str, session_id: str, all_chunks: List[Chunk], limit: int = 5) -> List[RAGResult]:
        query = RAGQuery(query_text=query_text, session_id=session_id, limit=limit)
        results = await self.engine.hybrid_search.search(query, all_chunks)
        return results

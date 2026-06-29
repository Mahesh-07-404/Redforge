from typing import List
from .engine import RAGEngine
from .contracts import Chunk, RAGQuery, RAGContext

class RAGPipeline:
    def __init__(self, engine: RAGEngine):
        self.engine = engine

    async def run_pipeline(self, query_text: str, session_id: str, all_chunks: List[Chunk], token_limit: int = 1000) -> RAGContext:
        query = RAGQuery(query_text=query_text, session_id=session_id)
        return await self.engine.query(query, all_chunks, token_limit=token_limit)

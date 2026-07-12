import logging

from .contracts import Chunk, RAGQuery, RAGResult
from .embedder import EmbeddingProvider
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class HybridSearch:
    def __init__(self, vector_store: VectorStore, embedding_provider: EmbeddingProvider):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider

    async def search(self, query: RAGQuery, all_chunks: list[Chunk]) -> list[RAGResult]:
        results: list[RAGResult] = []

        q_words = set(query.query_text.lower().split())
        for c in all_chunks:
            if query.session_id and c.session_id != query.session_id:
                continue

            content_words = set(c.content.lower().split())
            overlap = len(q_words.intersection(content_words))
            if overlap > 0:
                results.append(
                    RAGResult(chunk=c, score=float(overlap) / len(q_words), source_type=c.source)
                )

        try:
            emb = await self.embedding_provider.embed_text(query.query_text)
            vector_res = await self.vector_store.search_vector(emb, limit=query.limit)
            for chunk, score in vector_res:
                existing = next((r for r in results if r.chunk.id == chunk.id), None)
                if existing:
                    existing.score = max(existing.score, score)
                else:
                    results.append(RAGResult(chunk=chunk, score=score, source_type=chunk.source))
        except (
            Exception
        ) as exc:  # nosec B110 - vector search is best-effort; keyword results still returned
            logger.debug("Vector embedding search failed, using keyword results only: %s", exc)

        unique_results = []
        seen_ids = set()
        for r in results:
            if r.chunk.id not in seen_ids:
                seen_ids.add(r.chunk.id)
                unique_results.append(r)

        unique_results.sort(key=lambda x: x.score, reverse=True)
        return unique_results[: query.limit]

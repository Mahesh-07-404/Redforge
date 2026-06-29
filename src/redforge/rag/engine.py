from typing import List, Optional
from .contracts import RAGQuery, RAGResult, RAGContext, Chunk
from .embedder import EmbeddingProvider, MockEmbedder
from .vector_store import VectorStore, MemoryVectorStore
from .hybrid_search import HybridSearch
from .reranker import Reranker
from .context_builder import ContextBuilder
from .knowledge_base import KnowledgeBase
from .cache import RAGCache

class RAGEngine:
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        knowledge_base: Optional[KnowledgeBase] = None
    ):
        self.vector_store = vector_store or MemoryVectorStore()
        self.embedding_provider = embedding_provider or MockEmbedder()
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.hybrid_search = HybridSearch(self.vector_store, self.embedding_provider)
        self.cache = RAGCache()

    async def ingest_chunks(self, chunks: List[Chunk]):
        embeddings = await self.embedding_provider.embed_batch([c.content for c in chunks])
        await self.vector_store.add_chunks(chunks, embeddings)

    async def query(self, rag_query: RAGQuery, all_chunks: List[Chunk], token_limit: int = 1000) -> RAGContext:
        cache_key = f"query_{rag_query.session_id}_{rag_query.query_text}_{token_limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
            
        results = await self.hybrid_search.search(rag_query, all_chunks)
        reranked = Reranker.rerank(results, rag_query.query_text, rag_query.session_id)
        context = ContextBuilder.build_context(reranked, token_limit=token_limit)
        
        self.cache.set(cache_key, context)
        return context

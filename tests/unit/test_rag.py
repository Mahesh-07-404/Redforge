import pytest
import asyncio
from redforge.rag.contracts import Chunk, RAGQuery, RAGResult, RAGContext
from redforge.rag.chunker import ChunkEngine
from redforge.rag.embedder import MockEmbedder, OpenAIEmbedder, GeminiEmbedder
from redforge.rag.vector_store import MemoryVectorStore, SQLiteVectorStore
from redforge.rag.sources import MemorySourceProvider, SessionMemoryProvider
from redforge.rag.knowledge_base import KnowledgeBase
from redforge.rag.reranker import Reranker
from redforge.rag.hybrid_search import HybridSearch
from redforge.rag.context_builder import ContextBuilder
from redforge.rag.cache import RAGCache
from redforge.rag.engine import RAGEngine
from redforge.rag.manager import RAGManager
from redforge.rag.retriever import Retriever
from redforge.rag.pipeline import RAGPipeline

def test_chunking():
    text = "hello world this is a test of redforge rag system"
    chunks = ChunkEngine.chunk_text(text, "sess1", "test_source", chunk_size=3)
    assert len(chunks) > 0
    assert chunks[0].session_id == "sess1"
    assert chunks[0].source == "test_source"
    assert len(chunks[0].content.split()) <= 3
    assert chunks[0].hash is not None

@pytest.mark.asyncio
async def test_embedding_providers():
    mock_emb = MockEmbedder()
    openai_emb = OpenAIEmbedder(api_key="sk-test")
    gemini_emb = GeminiEmbedder()
    
    vec1 = await mock_emb.embed_text("test")
    assert len(vec1) == 128
    
    vec2 = await openai_emb.embed_text("test")
    assert len(vec2) == 128
    
    vec3 = await gemini_emb.embed_text("test")
    assert len(vec3) == 128

@pytest.mark.asyncio
async def test_vector_stores():
    store = MemoryVectorStore()
    chunk = Chunk(id="c1", session_id="s1", source="src", content="test content", hash="h1", timestamp="t1")
    await store.add_chunks([chunk], [[0.1] * 128])
    
    res = await store.search_vector([0.1] * 128, limit=1)
    assert len(res) == 1
    assert res[0][0].id == "c1"

def test_knowledge_base():
    kb = KnowledgeBase()
    chunk = Chunk(id="k1", session_id="s1", source="cve", content="CVE-2026-1234 detail", hash="h1", timestamp="t1")
    kb.register_collection("cve", [chunk])
    
    res = kb.search_collection("cve", "CVE-2026")
    assert len(res) == 1
    assert res[0].id == "k1"

def test_reranker():
    chunk1 = Chunk(id="c1", session_id="s1", source="src", content="term test", hash="h1", timestamp="t1")
    chunk2 = Chunk(id="c2", session_id="s2", source="src", content="term test", hash="h2", timestamp="t2")
    
    results = [
        RAGResult(chunk=chunk1, score=0.5, source_type="src"),
        RAGResult(chunk=chunk2, score=0.5, source_type="src")
    ]
    
    reranked = Reranker.rerank(results, "term test", "s1")
    assert reranked[0].chunk.id == "c1" # Should rank higher due to session overlap heuristic

def test_context_builder():
    chunk = Chunk(id="c1", session_id="s1", source="src", content="Hello RedForge RAG", hash="h1", timestamp="t1")
    res = [RAGResult(chunk=chunk, score=1.0, source_type="src")]
    
    context = ContextBuilder.build_context(res, token_limit=50)
    assert "Hello RedForge RAG" in context.context_text
    assert context.token_count > 0

def test_cache():
    cache = RAGCache(ttl_seconds=1)
    cache.set("key", "val")
    assert cache.get("key") == "val"
    
    cache.invalidate()
    assert cache.get("key") is None

@pytest.mark.asyncio
async def test_rag_engine_and_pipeline():
    engine = RAGEngine()
    chunk = Chunk(id="c1", session_id="sess1", source="src", content="some document text", hash="h1", timestamp="t1")
    
    await engine.ingest_chunks([chunk])
    
    query = RAGQuery(query_text="document", session_id="sess1")
    context = await engine.query(query, [chunk])
    
    assert "some document text" in context.context_text
    
    # Retriever test
    ret = Retriever(engine)
    ret_res = await ret.retrieve("document", "sess1", [chunk])
    assert len(ret_res) == 1
    
    # Pipeline test
    pipe = RAGPipeline(engine)
    pipe_res = await pipe.run_pipeline("document", "sess1", [chunk])
    assert "some document text" in pipe_res.context_text

@pytest.mark.asyncio
async def test_rag_manager():
    engine = RAGEngine()
    manager = RAGManager(engine)
    
    provider = MemorySourceProvider()
    manager.register_provider(provider)
    assert "memory" in manager.providers
    
    # Populate test (should be empty but run without errors)
    await manager.populate_engine_from_providers("sess1")

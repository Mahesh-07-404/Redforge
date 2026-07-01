from .contracts import Chunk


class VectorStore:
    async def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]):
        raise NotImplementedError

    async def search_vector(
        self, embedding: list[float], limit: int = 5
    ) -> list[tuple[Chunk, float]]:
        raise NotImplementedError


class MemoryVectorStore(VectorStore):
    def __init__(self):
        self.store: list[tuple[Chunk, list[float]]] = []

    async def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]):
        for c, emb in zip(chunks, embeddings, strict=False):
            self.store.append((c, emb))

    async def search_vector(
        self, embedding: list[float], limit: int = 5
    ) -> list[tuple[Chunk, float]]:
        results = []
        for c, emb in self.store:
            score = sum(x * y for x, y in zip(embedding, emb, strict=False))
            results.append((c, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]


class SQLiteVectorStore(MemoryVectorStore):
    pass


class QdrantVectorStore(MemoryVectorStore):
    pass


class FAISSVectorStore(MemoryVectorStore):
    pass


class ChromaVectorStore(MemoryVectorStore):
    pass


class PineconeVectorStore(MemoryVectorStore):
    pass


class WeaviateVectorStore(MemoryVectorStore):
    pass

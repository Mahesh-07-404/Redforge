class RAGError(Exception):
    """Base exception for RAG system"""

    pass


class ChunkError(RAGError):
    """Chunking errors"""

    pass


class EmbedError(RAGError):
    """Embedding generation errors"""

    pass


class RetrievalError(RAGError):
    """Retrieval errors"""

    pass

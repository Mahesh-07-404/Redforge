"""Memory module with vector storage and RAG"""

from redforge.memory.vector import (
    VectorStore,
    MemoryEntry,
    SearchResult,
    create_vector_store,
    SimpleVectorStore,
    QdrantVectorStore,
)
from redforge.memory.workspace import WorkspaceManager, Workspace
from redforge.memory.memory_manager import (
    WorkspaceMemoryManager,
    WorkspaceMemory,
    GlobalMemory,
)

__all__ = [
    "VectorStore",
    "MemoryEntry",
    "SearchResult",
    "create_vector_store",
    "SimpleVectorStore",
    "QdrantVectorStore",
    "WorkspaceManager",
    "Workspace",
    "WorkspaceMemoryManager",
    "WorkspaceMemory",
    "GlobalMemory",
]

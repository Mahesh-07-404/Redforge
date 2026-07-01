"""Memory module with vector storage and RAG"""

from redforge.memory.memory_manager import (
    GlobalMemory,
    WorkspaceMemory,
    WorkspaceMemoryManager,
)
from redforge.memory.vector import (
    MemoryEntry,
    QdrantVectorStore,
    SearchResult,
    SimpleVectorStore,
    VectorStore,
    create_vector_store,
)
from redforge.memory.workspace import Workspace, WorkspaceManager

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

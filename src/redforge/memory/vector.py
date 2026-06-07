"""Vector store manager supporting Qdrant and ChromaDB"""

import json
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class MemoryEntry:
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    workspace_id: Optional[str] = None
    entry_type: str = "memory"


@dataclass
class SearchResult:
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float


class VectorStore:
    """Abstract vector store interface"""
    
    def __init__(self, persist_dir: str, collection_name: str):
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        self.persist_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_available(self) -> bool:
        return False
    
    def add(self, entries: List[MemoryEntry]) -> List[str]:
        raise NotImplementedError
    
    def search(
        self,
        query: str,
        limit: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        raise NotImplementedError
    
    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        raise NotImplementedError
    
    def delete(self, entry_id: str) -> bool:
        raise NotImplementedError
    
    def list_entries(
        self,
        limit: int = 100,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        raise NotImplementedError
    
    def clear(self) -> None:
        raise NotImplementedError


class SimpleVectorStore(VectorStore):
    """Simple JSON-based vector store (fallback)"""
    
    def __init__(self, persist_dir: str, collection_name: str = "redforge_memory"):
        super().__init__(persist_dir, collection_name)
        self.storage_file = self.persist_dir / "simple_store.json"
        self._entries: Dict[str, MemoryEntry] = {}
        self._load()
    
    @property
    def is_available(self) -> bool:
        return True
    
    def _load(self) -> None:
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r") as f:
                    data = json.load(f)
                    for entry_data in data.get("entries", []):
                        self._entries[entry_data["id"]] = MemoryEntry(**entry_data)
            except:
                pass
    
    def _save(self) -> None:
        with open(self.storage_file, "w") as f:
            json.dump({
                "entries": [
                    {
                        "id": e.id,
                        "content": e.content,
                        "metadata": e.metadata,
                        "created_at": e.created_at.isoformat(),
                        "workspace_id": e.workspace_id,
                        "entry_type": e.entry_type
                    }
                    for e in self._entries.values()
                ]
            }, f, indent=2)
    
    def add(self, entries: List[MemoryEntry]) -> List[str]:
        ids = []
        for entry in entries:
            entry_id = entry.id or hashlib.md5(entry.content.encode()).hexdigest()
            entry.id = entry_id
            self._entries[entry_id] = entry
            ids.append(entry_id)
        self._save()
        return ids
    
    def search(
        self,
        query: str,
        limit: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        query_words = set(query.lower().split())
        results = []
        
        for entry in self._entries.values():
            if filter_dict:
                skip = False
                for key, value in filter_dict.items():
                    if entry.metadata.get(key) != value:
                        skip = True
                        break
                if skip:
                    continue
            
            content_words = set(entry.content.lower().split())
            matches = len(query_words & content_words)
            if matches > 0:
                results.append(SearchResult(
                    id=entry.id,
                    content=entry.content,
                    metadata=entry.metadata,
                    score=float(matches) / max(len(query_words), 1)
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        return self._entries.get(entry_id)
    
    def delete(self, entry_id: str) -> bool:
        if entry_id in self._entries:
            del self._entries[entry_id]
            self._save()
            return True
        return False
    
    def list_entries(
        self,
        limit: int = 100,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        entries = list(self._entries.values())
        
        if filter_dict:
            entries = [
                e for e in entries
                if all(e.metadata.get(k) == v for k, v in filter_dict.items())
            ]
        
        entries.sort(key=lambda x: x.created_at, reverse=True)
        return entries[:limit]
    
    def clear(self) -> None:
        self._entries.clear()
        self._save()


class ChromaVectorStore(VectorStore):
    """ChromaDB vector store implementation"""
    
    def __init__(
        self,
        persist_dir: str,
        collection_name: str = "redforge_memory",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        super().__init__(persist_dir, collection_name)
        
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.client = chromadb.PersistentClient(
                path=str(self.persist_dir / "chromadb"),
                settings=Settings(anonymized_telemetry=False)
            )
            
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "RedForge memory store"}
            )
            
            self._embedding_function = None
            self._embedding_model = embedding_model
            self._available = True
            
        except Exception as e:
            print(f"ChromaDB initialization failed: {e}")
            self.client = None
            self.collection = None
            self._available = False
    
    @property
    def is_available(self) -> bool:
        return self._available and self.client is not None
    
    def _get_embedding(self, texts: List[str]) -> List[List[float]]:
        try:
            from sentence_transformers import SentenceTransformer
            
            if self._embedding_function is None:
                self._embedding_function = SentenceTransformer(self._embedding_model)
            
            embeddings = self._embedding_function.encode(texts)
            return embeddings.tolist()
        except ImportError:
            import hashlib
            return [[float(ord(c)) / 255.0 for c in hashlib.md5(t.encode()).digest()[:50]] for t in texts]
        except Exception:
            return [[0.0] * 50 for _ in texts]
    
    def add(self, entries: List[MemoryEntry]) -> List[str]:
        if not self.is_available:
            return []
        
        ids = []
        documents = []
        metadatas = []
        
        for entry in entries:
            entry_id = entry.id or hashlib.md5(entry.content.encode()).hexdigest()
            ids.append(entry_id)
            documents.append(entry.content)
            metadatas.append({
                **entry.metadata,
                "workspace_id": entry.workspace_id,
                "entry_type": entry.entry_type,
                "created_at": entry.created_at.isoformat()
            })
        
        if documents:
            embeddings = self._get_embedding(documents)
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
        
        return ids
    
    def search(
        self,
        query: str,
        limit: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        if not self.is_available:
            return []
        
        try:
            query_embedding = self._get_embedding([query])[0]
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=filter_dict
            )
            
            search_results = []
            if results and results.get("ids"):
                for i in range(len(results["ids"][0])):
                    search_results.append(SearchResult(
                        id=results["ids"][0][i],
                        content=results["documents"][0][i],
                        metadata=results["metadatas"][0][i] if results.get("metadatas") else {},
                        score=float(results.get("distances", [[1.0]])[0][i]) if results.get("distances") else 1.0
                    ))
            
            return search_results
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        if not self.is_available:
            return None
        
        try:
            results = self.collection.get(ids=[entry_id])
            if results and results.get("ids"):
                return MemoryEntry(
                    id=results["ids"][0],
                    content=results["documents"][0],
                    metadata=results["metadatas"][0] if results.get("metadatas") else {},
                    created_at=datetime.fromisoformat(
                        results["metadatas"][0].get("created_at", datetime.now().isoformat())
                    ) if results.get("metadatas") else datetime.now(),
                    workspace_id=results["metadatas"][0].get("workspace_id") if results.get("metadatas") else None,
                    entry_type=results["metadatas"][0].get("entry_type", "memory") if results.get("metadatas") else "memory"
                )
        except:
            pass
        return None
    
    def delete(self, entry_id: str) -> bool:
        if not self.is_available:
            return False
        try:
            self.collection.delete(ids=[entry_id])
            return True
        except:
            return False
    
    def list_entries(
        self,
        limit: int = 100,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        if not self.is_available:
            return []
        
        try:
            results = self.collection.get(limit=limit, where=filter_dict)
            
            entries = []
            if results and results.get("ids"):
                for i in range(len(results["ids"])):
                    entries.append(MemoryEntry(
                        id=results["ids"][i],
                        content=results["documents"][i],
                        metadata=results["metadatas"][i] if results.get("metadatas") else {},
                        created_at=datetime.fromisoformat(
                            results["metadatas"][i].get("created_at", datetime.now().isoformat())
                        ) if results.get("metadatas") else datetime.now(),
                        workspace_id=results["metadatas"][i].get("workspace_id") if results.get("metadatas") else None,
                        entry_type=results["metadatas"][i].get("entry_type", "memory") if results.get("metadatas") else "memory"
                    ))
            
            return entries
        except:
            return []
    
    def clear(self) -> None:
        if self.is_available:
            try:
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.get_or_create_collection(self.collection_name)
            except:
                pass


def create_vector_store(
    vector_db: str = "chroma",
    persist_dir: str = "./workspaces",
    collection_name: str = "redforge_memory"
) -> VectorStore:
    """Factory function to create vector store"""
    
    if vector_db.lower() == "chroma":
        try:
            store = ChromaVectorStore(persist_dir, collection_name)
            if store.is_available:
                return store
        except:
            pass
    
    return SimpleVectorStore(persist_dir, collection_name)

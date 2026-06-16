import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from ..contracts.memory import MemoryEntry

class QdrantAdapter:
    def __init__(self, persist_dir: str):
        import os
        os.makedirs(persist_dir, exist_ok=True)
        self.client = QdrantClient(path=f"{persist_dir}/qdrant")

    def _ensure_collection(self, collection_name: str):
        collections = [c.name for c in self.client.get_collections().collections]
        if collection_name not in collections:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    def store(self, collection_name: str, entry: MemoryEntry):
        self._ensure_collection(collection_name)
        import hashlib
        base = [float(b) / 255.0 for b in hashlib.md5(entry.content.encode()).digest()]
        vector = base * 24
        
        entry_id = entry.id or str(uuid.uuid4())
        payload = {
            "content": entry.content,
            **entry.metadata
        }
        self.client.upsert(
            collection_name=collection_name,
            points=[PointStruct(id=entry_id, vector=vector, payload=payload)]
        )

    def retrieve(self, collection_name: str, query: str, top_k: int = 5) -> List[MemoryEntry]:
        self._ensure_collection(collection_name)
        import hashlib
        base = [float(b) / 255.0 for b in hashlib.md5(query.encode()).digest()]
        vector = base * 24
        
        response = self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=top_k
        )
        hits = response.points
        
        results = []
        for hit in hits:
            payload = hit.payload or {}
            content = payload.pop("content", "")
            results.append(MemoryEntry(
                id=str(hit.id),
                content=content,
                metadata=payload
            ))
        return results

    def drop_collection(self, collection_name: str):
        try:
            self.client.delete_collection(collection_name=collection_name)
        except Exception:
            pass

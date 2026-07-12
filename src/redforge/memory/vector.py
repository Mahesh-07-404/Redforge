"""Vector store manager supporting Qdrant and ChromaDB"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    workspace_id: str | None = None
    entry_type: str = "memory"


@dataclass
class SearchResult:
    id: str
    content: str
    metadata: dict[str, Any]
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

    def add(self, entries: list[MemoryEntry]) -> list[str]:
        raise NotImplementedError

    def search(
        self, query: str, limit: int = 5, filter_dict: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        raise NotImplementedError

    def get(self, entry_id: str) -> MemoryEntry | None:
        raise NotImplementedError

    def delete(self, entry_id: str) -> bool:
        raise NotImplementedError

    def list_entries(
        self, limit: int = 100, filter_dict: dict[str, Any] | None = None
    ) -> list[MemoryEntry]:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class SimpleVectorStore(VectorStore):
    """Simple JSON-based vector store (fallback)"""

    def __init__(self, persist_dir: str, collection_name: str = "redforge_memory"):
        super().__init__(persist_dir, collection_name)
        self.storage_file = self.persist_dir / "simple_store.json"
        self._entries: dict[str, MemoryEntry] = {}
        self._load()

    @property
    def is_available(self) -> bool:
        return True

    def _load(self) -> None:
        if self.storage_file.exists():
            try:
                with open(self.storage_file) as f:
                    data = json.load(f)
                    for entry_data in data.get("entries", []):
                        self._entries[entry_data["id"]] = MemoryEntry(**entry_data)
            except (
                OSError,
                ValueError,
                KeyError,
            ) as exc:  # nosec B110 - best-effort persistent store load
                logger.debug(
                    "SimpleVectorStore failed to load '%s', starting empty: %s",
                    self.storage_file,
                    exc,
                )

    def _save(self) -> None:
        with open(self.storage_file, "w") as f:
            json.dump(
                {
                    "entries": [
                        {
                            "id": e.id,
                            "content": e.content,
                            "metadata": e.metadata,
                            "created_at": e.created_at.isoformat(),
                            "workspace_id": e.workspace_id,
                            "entry_type": e.entry_type,
                        }
                        for e in self._entries.values()
                    ]
                },
                f,
                indent=2,
            )

    def add(self, entries: list[MemoryEntry]) -> list[str]:
        ids = []
        for entry in entries:
            entry_id = entry.id or hashlib.md5(entry.content.encode(), usedforsecurity=False).hexdigest()
            entry.id = entry_id
            self._entries[entry_id] = entry
            ids.append(entry_id)
        self._save()
        return ids

    def search(
        self, query: str, limit: int = 5, filter_dict: dict[str, Any] | None = None
    ) -> list[SearchResult]:
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
                results.append(
                    SearchResult(
                        id=entry.id,
                        content=entry.content,
                        metadata=entry.metadata,
                        score=float(matches) / max(len(query_words), 1),
                    )
                )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def get(self, entry_id: str) -> MemoryEntry | None:
        return self._entries.get(entry_id)

    def delete(self, entry_id: str) -> bool:
        if entry_id in self._entries:
            del self._entries[entry_id]
            self._save()
            return True
        return False

    def list_entries(
        self, limit: int = 100, filter_dict: dict[str, Any] | None = None
    ) -> list[MemoryEntry]:
        entries = list(self._entries.values())

        if filter_dict:
            entries = [
                e for e in entries if all(e.metadata.get(k) == v for k, v in filter_dict.items())
            ]

        entries.sort(key=lambda x: x.created_at, reverse=True)
        return entries[:limit]

    def clear(self) -> None:
        self._entries.clear()
        self._save()


class QdrantVectorStore(VectorStore):
    """Qdrant vector store implementation"""

    def __init__(
        self,
        persist_dir: str,
        collection_name: str = "redforge_memory",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        super().__init__(persist_dir, collection_name)
        self.client: Any = None

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http.models import Distance, VectorParams

            self.client = QdrantClient(path=str(self.persist_dir / "qdrant"))
            self._embedding_model = embedding_model
            self._embedding_function = None

            # Create collection if it doesn't exist
            collections = [c.name for c in self.client.get_collections().collections]
            if self.collection_name not in collections:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )

            self._available = True

        except Exception as e:
            print(f"Qdrant initialization failed: {e}")
            self.client = None
            self._available = False

    def _get_embedding(self, texts: list[str]) -> list[list[float]]:
        try:
            from sentence_transformers import SentenceTransformer

            emb_func = self._embedding_function
            if emb_func is None:
                emb_func = SentenceTransformer(self._embedding_model)
                self._embedding_function = emb_func

            embeddings = emb_func.encode(texts)
            return cast(list[list[float]], embeddings.tolist())
        except ImportError:
            import hashlib

            # Fallback embedding to match Qdrant size 384
            # We repeat the md5 hash values to fill 384 dimensions
            # fmt: off
            base = [
                float(c) / 255.0
                for c in hashlib.md5(texts[0].encode(), usedforsecurity=False).digest()
            ]  # 16 floats
            # fmt: on
            full = base * 24  # 16 * 24 = 384
            return [full for _ in texts]
        except Exception:
            return [[0.0] * 384 for _ in texts]

    @property
    def is_available(self) -> bool:
        return self._available and self.client is not None

    def add(self, entries: list[MemoryEntry]) -> list[str]:
        if not self.is_available:
            return []

        import uuid

        from qdrant_client.http.models import PointStruct

        ids = []
        points = []
        documents = []

        for entry in entries:
            # Qdrant requires UUIDs or integers
            try:
                entry_uuid = str(uuid.UUID(entry.id))
            except (ValueError, TypeError, AttributeError):
                # If not a valid UUID, generate one based on the ID or content
                hash_id = hashlib.md5((entry.id or entry.content).encode(), usedforsecurity=False).hexdigest()
                entry_uuid = str(uuid.UUID(hash_id))

            entry.id = entry_uuid
            ids.append(entry_uuid)
            documents.append(entry.content)

        if documents:
            embeddings = self._get_embedding(documents)

            for i, entry in enumerate(entries):
                payload = {
                    "content": entry.content,
                    **entry.metadata,
                    "workspace_id": entry.workspace_id,
                    "entry_type": entry.entry_type,
                    "created_at": entry.created_at.isoformat(),
                }
                points.append(PointStruct(id=ids[i], vector=embeddings[i], payload=payload))

            self.client.upsert(collection_name=self.collection_name, points=points)

        return ids

    def search(
        self, query: str, limit: int = 5, filter_dict: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        if not self.is_available:
            return []

        from qdrant_client.http.models import FieldCondition, Filter, MatchValue

        query_filter = None
        if filter_dict:
            conditions: list[Any] = [
                FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filter_dict.items()
            ]
            query_filter = Filter(must=conditions)

        query_vector = self._get_embedding([query])[0]

        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
        )

        results = []
        for hit in hits:
            payload = hit.payload or {}
            content = payload.pop("content", "")
            results.append(
                SearchResult(id=str(hit.id), content=content, metadata=payload, score=hit.score)
            )

        return results

    def get(self, entry_id: str) -> MemoryEntry | None:
        if not self.is_available:
            return None

        import uuid

        try:
            entry_uuid = str(uuid.UUID(entry_id))
        except ValueError:
            return None

        results = self.client.retrieve(collection_name=self.collection_name, ids=[entry_uuid])

        if not results:
            return None

        payload = results[0].payload or {}
        content = payload.pop("content", "")

        return MemoryEntry(
            id=str(results[0].id),
            content=content,
            metadata=payload,
            created_at=datetime.fromisoformat(
                payload.get("created_at", datetime.now().isoformat())
            ),
            workspace_id=payload.get("workspace_id"),
            entry_type=payload.get("entry_type", "memory"),
        )

    def delete(self, entry_id: str) -> bool:
        if not self.is_available:
            return False

        import uuid

        try:
            entry_uuid = str(uuid.UUID(entry_id))
        except ValueError:
            return False

        self.client.delete(collection_name=self.collection_name, points_selector=[entry_uuid])
        return True

    def list_entries(
        self, limit: int = 100, filter_dict: dict[str, Any] | None = None
    ) -> list[MemoryEntry]:
        if not self.is_available:
            return []

        from qdrant_client.http.models import FieldCondition, Filter, MatchValue

        query_filter = None
        if filter_dict:
            conditions: list[Any] = [
                FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filter_dict.items()
            ]
            query_filter = Filter(must=conditions)

        records, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

        entries = []
        for r in records:
            payload = r.payload or {}
            content = payload.pop("content", "")
            entries.append(
                MemoryEntry(
                    id=str(r.id),
                    content=content,
                    metadata=payload,
                    created_at=datetime.fromisoformat(
                        payload.get("created_at", datetime.now().isoformat())
                    ),
                    workspace_id=payload.get("workspace_id"),
                    entry_type=payload.get("entry_type", "memory"),
                )
            )

        return entries

    def clear(self) -> None:
        if self.is_available:
            try:
                self.client.delete_collection(collection_name=self.collection_name)
                from qdrant_client.http.models import Distance, VectorParams

                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
            except Exception as exc:  # nosec B110 - best-effort Qdrant collection recreation
                logger.debug(
                    "QdrantVectorStore clear failed for '%s': %s", self.collection_name, exc
                )


def create_vector_store(
    vector_db: str = "qdrant",
    persist_dir: str = "./workspaces",
    collection_name: str = "redforge_memory",
) -> VectorStore:
    """Factory function to create vector store"""

    if vector_db.lower() == "qdrant":
        try:
            store = QdrantVectorStore(persist_dir, collection_name)
            if store.is_available:
                return store
        except Exception as exc:  # nosec B110 - Qdrant unavailable; fall back to SimpleVectorStore
            logger.debug("Qdrant store creation failed, using SimpleVectorStore: %s", exc)

    return SimpleVectorStore(persist_dir, collection_name)

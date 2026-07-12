import logging
import uuid
from typing import Any, cast

from ..contracts.memory import MemoryEntry

logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, PointStruct, VectorParams

    HAS_QDRANT = True
except ImportError:

    class DummyQdrantClient:
        def __init__(self, *args, **kwargs):
            pass

        def get_collections(self, *args, **kwargs):
            class DummyCollectionList:
                collections = []

            return DummyCollectionList()

        def create_collection(self, *args, **kwargs):
            pass

        def upsert(self, *args, **kwargs):
            pass

        def query_points(self, *args, **kwargs):
            class DummyPoints:
                points = []

            return DummyPoints()

        def delete_collection(self, *args, **kwargs):
            pass

    class DummyDistance:
        COSINE = "Cosine"

    class DummyVectorParams:
        def __init__(self, *args, **kwargs):
            pass

    class DummyPointStruct:
        def __init__(self, *args, **kwargs):
            pass

    HAS_QDRANT = False
    QdrantClient = DummyQdrantClient  # type: ignore[misc, assignment]
    Distance = DummyDistance  # type: ignore[misc, assignment]
    VectorParams = DummyVectorParams  # type: ignore[misc, assignment]
    PointStruct = DummyPointStruct  # type: ignore[misc, assignment]


class QdrantAdapter:
    def __init__(self, persist_dir: str):
        import os

        os.makedirs(persist_dir, exist_ok=True)
        self.persist_dir = persist_dir
        if HAS_QDRANT:
            self.client = QdrantClient(path=f"{persist_dir}/qdrant")
        else:
            self.client = QdrantClient()

    def _ensure_collection(self, collection_name: str):
        if not HAS_QDRANT:
            return
        collections = [c.name for c in self.client.get_collections().collections]
        if collection_name not in collections:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=cast(Any, VectorParams)(size=384, distance=Distance.COSINE),
            )

    def store(self, collection_name: str, entry: MemoryEntry):
        if not HAS_QDRANT:
            import json
            import os

            fallback_file = os.path.join(self.persist_dir, "fallback_store.json")
            data = {}
            if os.path.exists(fallback_file):
                try:
                    with open(fallback_file) as f:
                        data = json.load(f)
                except (OSError, ValueError) as exc:  # nosec B110 - best-effort fallback file read
                    logger.debug("Fallback store read failed, starting with empty store: %s", exc)
            collection_data = data.setdefault(collection_name, {})
            entry_id = entry.id or str(uuid.uuid4())
            collection_data[entry_id] = {
                "id": entry_id,
                "content": entry.content,
                "metadata": entry.metadata or {},
            }
            try:
                with open(fallback_file, "w") as f:
                    json.dump(data, f)
            except (OSError, ValueError) as exc:  # nosec B110 - best-effort fallback file write
                logger.warning(
                    "Fallback store write failed for collection '%s': %s", collection_name, exc
                )
            return

        self._ensure_collection(collection_name)
        import hashlib

        base = [float(b) / 255.0 for b in hashlib.md5(entry.content.encode()).digest()]
        vector = base * 24

        entry_id = entry.id or str(uuid.uuid4())
        payload = {"content": entry.content, **(entry.metadata or {})}
        self.client.upsert(
            collection_name=collection_name,
            points=[cast(Any, PointStruct)(id=entry_id, vector=vector, payload=payload)],
        )

    def retrieve(self, collection_name: str, query: str, top_k: int = 5) -> list[MemoryEntry]:
        if not HAS_QDRANT:
            import json
            import os

            fallback_file = os.path.join(self.persist_dir, "fallback_store.json")
            if not os.path.exists(fallback_file):
                return []
            try:
                with open(fallback_file) as f:
                    data = json.load(f)
            except (OSError, ValueError) as exc:  # nosec B110 - best-effort fallback file read
                logger.debug(
                    "Fallback retrieve read failed for collection '%s': %s", collection_name, exc
                )
                return []
            collection_data = data.get(collection_name, {})
            results = []
            words = query.lower().split()
            for _entry_id, val in collection_data.items():
                content = val.get("content", "")
                score = sum(1 for w in words if w in content.lower())
                results.append((score, val))

            results.sort(key=lambda x: x[0], reverse=True)

            mapped = []
            for _, val in results[:top_k]:
                mapped.append(
                    MemoryEntry(
                        id=val.get("id"),
                        content=val.get("content"),
                        metadata=val.get("metadata", {}),
                    )
                )
            return mapped

        self._ensure_collection(collection_name)
        import hashlib

        base = [float(b) / 255.0 for b in hashlib.md5(query.encode()).digest()]
        vector = base * 24

        response = self.client.query_points(
            collection_name=collection_name, query=vector, limit=top_k
        )
        hits = response.points

        query_results = []
        for hit in hits:
            payload = hit.payload or {}
            content = payload.pop("content", "")
            query_results.append(MemoryEntry(id=str(hit.id), content=content, metadata=payload))
        return query_results

    def drop_collection(self, collection_name: str):
        if not HAS_QDRANT:
            import json
            import os

            fallback_file = os.path.join(self.persist_dir, "fallback_store.json")
            if os.path.exists(fallback_file):
                try:
                    with open(fallback_file) as f:
                        data = json.load(f)
                    if collection_name in data:
                        del data[collection_name]
                        with open(fallback_file, "w") as f:
                            json.dump(data, f)
                except (
                    OSError,
                    ValueError,
                ) as exc:  # nosec B110 - best-effort fallback collection drop
                    logger.debug(
                        "Fallback drop_collection failed for '%s': %s", collection_name, exc
                    )
            return

        try:
            self.client.delete_collection(collection_name=collection_name)
        except Exception as exc:  # nosec B110 - best-effort Qdrant collection deletion
            logger.debug("Qdrant delete_collection failed for '%s': %s", collection_name, exc)

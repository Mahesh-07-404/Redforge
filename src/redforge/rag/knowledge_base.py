from .contracts import Chunk


class KnowledgeBase:
    def __init__(self):
        self.collections: dict[str, list[Chunk]] = {}

    def register_collection(self, name: str, chunks: list[Chunk]):
        self.collections[name] = chunks

    def search_collection(self, collection_name: str, query: str, limit: int = 5) -> list[Chunk]:
        chunks = self.collections.get(collection_name, [])
        q_lower = query.lower()
        results = [c for c in chunks if q_lower in c.content.lower()]
        return results[:limit]

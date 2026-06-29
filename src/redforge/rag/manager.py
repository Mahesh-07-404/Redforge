from typing import List, Dict
from .sources import SourceProvider
from .engine import RAGEngine

class RAGManager:
    def __init__(self, engine: RAGEngine):
        self.engine = engine
        self.providers: Dict[str, SourceProvider] = {}

    def register_provider(self, provider: SourceProvider):
        self.providers[provider.get_name()] = provider

    async def populate_engine_from_providers(self, session_id: str):
        all_chunks = []
        for name, provider in self.providers.items():
            chunks = await provider.fetch_chunks(session_id)
            all_chunks.extend(chunks)
        if all_chunks:
            await self.engine.ingest_chunks(all_chunks)

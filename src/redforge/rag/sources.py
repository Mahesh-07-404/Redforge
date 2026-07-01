from .contracts import Chunk


class SourceProvider:
    def get_name(self) -> str:
        raise NotImplementedError

    async def fetch_chunks(self, session_id: str) -> list[Chunk]:
        raise NotImplementedError


class MemorySourceProvider(SourceProvider):
    def get_name(self) -> str:
        return "memory"

    async def fetch_chunks(self, session_id: str) -> list[Chunk]:
        return []


class SessionMemoryProvider(SourceProvider):
    def get_name(self) -> str:
        return "session_memory"

    async def fetch_chunks(self, session_id: str) -> list[Chunk]:
        return []


class EntityMemoryProvider(SourceProvider):
    def get_name(self) -> str:
        return "entity_memory"

    async def fetch_chunks(self, session_id: str) -> list[Chunk]:
        return []


class TimelineMemoryProvider(SourceProvider):
    def get_name(self) -> str:
        return "timeline_memory"

    async def fetch_chunks(self, session_id: str) -> list[Chunk]:
        return []


class EvidenceStoreProvider(SourceProvider):
    def get_name(self) -> str:
        return "evidence_store"

    async def fetch_chunks(self, session_id: str) -> list[Chunk]:
        return []


class ReportsProvider(SourceProvider):
    def get_name(self) -> str:
        return "reports"

    async def fetch_chunks(self, session_id: str) -> list[Chunk]:
        return []


class MarkdownSkillsProvider(SourceProvider):
    def get_name(self) -> str:
        return "markdown_skills"

    async def fetch_chunks(self, session_id: str) -> list[Chunk]:
        return []


class DocumentationProvider(SourceProvider):
    def get_name(self) -> str:
        return "documentation"

    async def fetch_chunks(self, session_id: str) -> list[Chunk]:
        return []

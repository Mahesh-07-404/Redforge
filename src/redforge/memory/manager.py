import logging

from ..contracts.memory import ContextBudget, ContextBundle, MemoryEntry
from .context_budget import ContextBudgetManager
from .vector_store import QdrantAdapter

logger = logging.getLogger(__name__)


class MemoryManager:
    def __init__(self, persist_dir: str = "./data"):
        self.adapter = QdrantAdapter(persist_dir)
        self.budget_manager = ContextBudgetManager()

    def store(self, session_id: str, entry: MemoryEntry, long_term: bool = False) -> None:
        collection = "redforge_longterm" if long_term else f"redforge_{session_id[:8]}"
        self.adapter.store(collection, entry)

    def retrieve(self, session_id: str, query: str, top_k: int = 5) -> list[MemoryEntry]:
        ephemeral = self.adapter.retrieve(f"redforge_{session_id[:8]}", query, top_k)
        longterm = self.adapter.retrieve("redforge_longterm", query, top_k)
        # simple dedup and truncation
        all_results = ephemeral + longterm
        return all_results[:top_k]

    def flush_session(self, session_id: str) -> None:
        self.adapter.drop_collection(f"redforge_{session_id[:8]}")

    def build_context(self, intent: str, skills: list[str]) -> ContextBundle:
        budget = self.budget_manager.get_budget()

        # Retrieve and render memory context synthesizer template
        from redforge.prompt_library.registry import get_prompt_library_registry
        from redforge.prompts.registry import get_prompt_registry

        try:
            registry = get_prompt_registry()
            rendered = registry.render(
                "memory_context_synthesizer",
                chat_history="Intended activity matching: " + intent,
                existing_memory="Active Skills: " + ", ".join(skills),
            )
            logger.debug("Rendered memory context synthesizer:\n%s", rendered)
        except Exception as e:
            logger.debug("Failed to render memory prompt: %s", e)

        try:
            lib_registry = get_prompt_library_registry()
            rendered_gen = lib_registry.render(
                "memory_context_keeper",
                chat_history="Intended activity matching: " + intent,
                current_summary="Active Skills: " + ", ".join(skills),
            )
            logger.debug("Rendered memory context keeper:\n%s", rendered_gen)
        except Exception as e:
            logger.debug("Failed to render general memory prompt: %s", e)

        content = "\n".join(skills)[: budget.system_prompt]
        return ContextBundle(content=content, total_tokens=len(content.split()))

    def get_budget(self) -> ContextBudget:
        return self.budget_manager.get_budget()

    def get_context_for_llm(self, query: str, session_id: str, max_entries: int = 5) -> str:
        results = self.retrieve(session_id, query, top_k=max_entries)
        parts = [f"- {r.content[:200]}..." for r in results]
        return "\n".join(parts)

    def add_finding(
        self,
        session_id: str,
        finding_type: str,
        title: str,
        description: str,
        severity: str,
        target: str,
    ) -> None:
        import uuid

        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=f"Finding: {title}\nType: {finding_type}\nSeverity: {severity}\n{description}",
            metadata={"type": "finding", "severity": severity, "target": target},
        )
        self.store(session_id, entry, long_term=True)

    def add_session(self, session_id: str, user_input: str, response: str) -> None:
        import uuid

        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=f"User: {user_input}\nAssistant: {response}",
            metadata={"type": "session"},
        )
        self.store(session_id, entry)


MemoryService = MemoryManager

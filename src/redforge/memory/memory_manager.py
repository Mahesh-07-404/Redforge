"""RedForge Memory Manager Component"""

import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

from redforge.memory.vector import (
    MemoryEntry,
    SearchResult,
    create_vector_store,
)


class MemoryManager:
    """Three-layered memory management using SQLite for long-term persistence"""

    def __init__(self, db_path: str | None = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Create a local redforge.db in workspace directory
            self.db_path = Path("./redforge.db")

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

        # Short term in-memory layer
        self.short_term: dict[str, Any] = {}
        # Workspace layer (current session cache)
        self.workspace: dict[str, Any] = {"target": None, "findings": [], "notes": []}

    def _init_db(self) -> None:
        """Initialize SQLite database tables for long term storage"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host TEXT UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    severity TEXT,
                    category TEXT,
                    description TEXT,
                    target TEXT,
                    evidence TEXT,
                    status TEXT,
                    timestamp TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    target TEXT,
                    content TEXT,
                    format TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    name TEXT PRIMARY KEY,
                    target TEXT,
                    state_json TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    # Targets
    def add_target(self, host: str, description: str = "") -> None:
        self.workspace["target"] = host
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO targets (host, description) VALUES (?, ?)",
                (host, description),
            )
            conn.commit()

    def get_targets(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM targets")
            return [dict(row) for row in cursor.fetchall()]

    # Findings
    def add_finding(self, finding: dict[str, Any]) -> None:
        fid = finding.get("id")
        if not any(f.get("id") == fid for f in self.workspace["findings"]):
            self.workspace["findings"].append(finding)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO findings 
                   (id, title, severity, category, description, target, evidence, status, timestamp) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    fid,
                    finding.get("title"),
                    finding.get("severity"),
                    finding.get("category"),
                    finding.get("description"),
                    finding.get("target"),
                    json.dumps(finding.get("evidence")),
                    finding.get("status"),
                    finding.get("timestamp"),
                ),
            )
            conn.commit()

    def get_findings(self, verified_only: bool = False) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if verified_only:
                cursor.execute("SELECT * FROM findings WHERE status = 'VERIFIED'")
            else:
                cursor.execute("SELECT * FROM findings")
            findings = []
            for row in cursor.fetchall():
                f = dict(row)
                try:
                    f["evidence"] = json.loads(f["evidence"]) if f["evidence"] else None
                except (
                    ValueError,
                    TypeError,
                ) as exc:  # nosec B110 - best-effort evidence JSON decode
                    logger.debug(
                        "Failed to decode evidence JSON for finding '%s': %s", f.get("id"), exc
                    )
                findings.append(f)
            return findings

    # Reports
    def save_report(self, title: str, target: str, content: str, report_format: str = "md") -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reports (title, target, content, format) VALUES (?, ?, ?, ?)",
                (title, target, content, report_format),
            )
            conn.commit()

    # Notes
    def add_note(self, content: str) -> None:
        self.workspace["notes"].append(content)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO notes (content) VALUES (?)", (content,))
            conn.commit()

    def get_notes(self) -> list[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM notes")
            return [row[0] for row in cursor.fetchall()]

    # Workspace management
    def clear_workspace(self) -> None:
        self.workspace = {"target": None, "findings": [], "notes": []}


# ---------------------------------------------------------------------------
# Legacy Compatibility Classes
# ---------------------------------------------------------------------------


@dataclass
class WorkspaceMemory:
    """Memory context for a workspace"""

    workspace_id: str
    session_history: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    context_summary: str = ""


class WorkspaceMemoryManager:
    """Manages workspace memory with RAG capabilities (legacy wrapper delegating to SQLite)"""

    def __init__(
        self, workspace_id: str, persist_dir: str = "./workspaces", vector_db: str = "simple"
    ):
        self.workspace_id = workspace_id
        self.persist_dir = Path(persist_dir) / workspace_id
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.persist_dir / "redforge.db"

        self.sqlite_mm = MemoryManager(db_path=str(self.db_path))

        self.vector_store = create_vector_store(
            vector_db=vector_db,
            persist_dir=str(self.persist_dir),
            collection_name=f"redforge_memory_{workspace_id}",
        )

        self._memory = WorkspaceMemory(workspace_id=workspace_id)
        self._load()

    def _load(self) -> None:
        """Load memory from SQLite database and index files"""
        findings = self.sqlite_mm.get_findings()
        notes = self.sqlite_mm.get_notes()

        # Load session history from SQLite sessions table
        session_history = []
        with sqlite3.connect(self.sqlite_mm.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state_json FROM sessions")
            for row in cursor.fetchall():
                try:
                    state = json.loads(row[0])
                    if "session_entry" in state:
                        session_history.append(state["session_entry"])
                except (
                    ValueError,
                    KeyError,
                ) as exc:  # nosec B110 - best-effort session JSON decode
                    logger.debug("Failed to decode session state JSON: %s", exc)

        self._memory = WorkspaceMemory(
            workspace_id=self.workspace_id,
            session_history=session_history,
            findings=findings,
            notes=notes,
            context_summary="",
        )

    def _save(self) -> None:
        """Commit changes to SQLite (already done in add_ methods)"""
        pass

    def add_session(self, user_input: str, response: str, metadata: dict | None = None) -> str:
        """Add a session exchange to memory"""
        session_id = str(uuid.uuid4())
        session_entry = {
            "id": session_id,
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "response": response,
            "metadata": metadata or {},
        }

        self._memory.session_history.append(session_entry)

        # Save to SQLite sessions table
        with sqlite3.connect(self.sqlite_mm.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO sessions (name, target, state_json) VALUES (?, ?, ?)",
                (session_id, "", json.dumps({"session_entry": session_entry})),
            )
            conn.commit()

        # Add to vector store for RAG
        entry = MemoryEntry(
            id=session_id,
            content=f"User: {user_input}\nAssistant: {response}",
            metadata={
                "type": "session",
                "workspace_id": self.workspace_id,
                "timestamp": session_entry["timestamp"],
            },
            workspace_id=self.workspace_id,
            entry_type="session",
        )
        self.vector_store.add([entry])
        return session_id

    def add_finding(
        self,
        finding_type: str,
        title: str,
        description: str,
        severity: str = "medium",
        target: str = "",
        evidence: dict | None = None,
    ) -> str:
        """Add a security finding"""
        finding_id = str(uuid.uuid4())

        finding = {
            "id": finding_id,
            "timestamp": datetime.now().isoformat(),
            "type": finding_type,
            "title": title,
            "description": description,
            "severity": severity,
            "target": target,
            "evidence": evidence or {},
            "status": "VERIFIED" if evidence else "UNVERIFIED",
        }

        self._memory.findings.append(finding)
        self.sqlite_mm.add_finding(finding)

        entry = MemoryEntry(
            id=finding_id,
            content=f"Finding: {title}\nType: {finding_type}\nSeverity: {severity}\n{description}",
            metadata={
                "type": "finding",
                "finding_type": finding_type,
                "severity": severity,
                "workspace_id": self.workspace_id,
            },
            workspace_id=self.workspace_id,
            entry_type="finding",
        )
        self.vector_store.add([entry])
        return finding_id

    def add_note(self, note: str) -> str:
        """Add a note to memory"""
        note_id = str(uuid.uuid4())
        self._memory.notes.append(note)
        self.sqlite_mm.add_note(note)

        entry = MemoryEntry(
            id=note_id,
            content=f"Note: {note}",
            metadata={"type": "note", "workspace_id": self.workspace_id},
            workspace_id=self.workspace_id,
            entry_type="note",
        )
        self.vector_store.add([entry])
        return note_id

    def update_context_summary(self, summary: str) -> None:
        self._memory.context_summary = summary

    def search(
        self, query: str, limit: int = 5, entry_type: str | None = None
    ) -> list[SearchResult]:
        filter_dict = {"workspace_id": self.workspace_id}
        if entry_type:
            filter_dict["type"] = entry_type
        return self.vector_store.search(query, limit=limit, filter_dict=filter_dict)

    def get_context_for_llm(self, query: str = "", max_entries: int = 10) -> str:
        context_parts = []
        context_parts.append(f"## Workspace: {self.workspace_id}")

        if self._memory.context_summary:
            context_parts.append(f"\n### Context Summary\n{self._memory.context_summary}")

        if query:
            relevant_entries = self.search(query, limit=max_entries)
            if relevant_entries:
                context_parts.append(f"\n### Relevant Memory (for: {query})")
                for entry in relevant_entries[:5]:
                    context_parts.append(f"- {entry.content[:200]}...")

        recent_sessions = self._memory.session_history[-3:]
        if recent_sessions:
            context_parts.append("\n### Recent Sessions")
            for session in recent_sessions:
                context_parts.append(
                    f"- [{session['timestamp']}] User asked about: {session['user_input'][:50]}..."
                )

        recent_findings = self._memory.findings[-5:]
        if recent_findings:
            context_parts.append("\n### Recent Findings")
            for finding in recent_findings:
                context_parts.append(f"- [{finding['severity'].upper()}] {finding['title']}")

        return "\n".join(context_parts)

    def get_stats(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "total_sessions": len(self._memory.session_history),
            "total_findings": len(self._memory.findings),
            "total_notes": len(self._memory.notes),
            "has_summary": bool(self._memory.context_summary),
            "vector_store_available": self.vector_store.is_available,
            "indexed_entries": len(self.vector_store.list_entries()),
        }

    def list_findings(
        self, severity: str | None = None, finding_type: str | None = None
    ) -> list[dict[str, Any]]:
        findings = self._memory.findings
        if severity:
            findings = [f for f in findings if f.get("severity") == severity]
        if finding_type:
            findings = [f for f in findings if f.get("type") == finding_type]
        return sorted(findings, key=lambda x: x.get("timestamp", ""), reverse=True)

    def list_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        return sorted(
            self._memory.session_history, key=lambda x: x.get("timestamp", ""), reverse=True
        )[:limit]

    def clear(self) -> None:
        self._memory = WorkspaceMemory(workspace_id=self.workspace_id)
        self.sqlite_mm.clear_workspace()
        self.vector_store.clear()


class GlobalMemory:
    """Global memory manager for all workspaces"""

    def __init__(self, persist_dir: str = "./workspaces", vector_db: str = "simple"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db = vector_db

        self.global_store = create_vector_store(
            vector_db=vector_db,
            persist_dir=str(self.persist_dir),
            collection_name="redforge_global",
        )

    def add_global_memory(
        self, content: str, memory_type: str = "general", tags: list[str] | None = None
    ) -> str:
        memory_id = str(uuid.uuid4())
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            metadata={"type": memory_type, "tags": tags or [], "global": True},
            entry_type=memory_type,
        )
        self.global_store.add([entry])
        return memory_id

    def search_global(self, query: str, limit: int = 5) -> list[SearchResult]:
        return self.global_store.search(query, limit=limit)

    def get_context(self, query: str = "") -> str:
        context_parts = []
        context_parts.append("## Global Knowledge Base")

        if query:
            results = self.search_global(query, limit=10)
            if results:
                context_parts.append(f"\n### Relevant Knowledge (for: {query})")
                for result in results:
                    context_parts.append(f"- {result.content[:200]}...")

        return "\n".join(context_parts)

"""Session management service for RedForge."""

import builtins
import json
import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Any

from ..contracts.session import Session, TargetState

logger = logging.getLogger(__name__)


class SessionStore:
    """Manages SQLite database storage for sessions, findings, and metadata."""

    def __init__(self, db_path: str = "sessions.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    mode TEXT,
                    target TEXT,
                    autonomy TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    status TEXT DEFAULT 'active',
                    metadata TEXT DEFAULT '{}',
                    memory_namespace TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    severity TEXT,
                    title TEXT,
                    evidence TEXT,
                    created_at TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    session_id TEXT,
                    key TEXT,
                    value TEXT,
                    PRIMARY KEY (session_id, key),
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)

            # Migration check to add columns if they do not exist
            cursor = conn.execute("PRAGMA table_info(sessions)")
            columns = [row[1] for row in cursor.fetchall()]
            if "status" not in columns:
                conn.execute("ALTER TABLE sessions ADD COLUMN status TEXT DEFAULT 'active'")
            if "metadata" not in columns:
                conn.execute("ALTER TABLE sessions ADD COLUMN metadata TEXT DEFAULT '{}'")
            if "memory_namespace" not in columns:
                conn.execute("ALTER TABLE sessions ADD COLUMN memory_namespace TEXT")
            conn.commit()


class SessionService:
    """Core Session Service for creating, loading, updating, and listing agent sessions."""

    def __init__(self, store: SessionStore | None = None):
        self.store = store or SessionStore()

    def create(
        self,
        mode: str,
        target: str | None,
        autonomy: str,
        session_id: str | None = None,
        name: str = "",
    ) -> Session:
        sid = session_id or str(uuid.uuid4())
        memory_namespace = f"session_{sid[:8]}"
        now = datetime.now()
        status = "active"

        # Serialize target if complex
        target_str = None
        meta = {"name": name}
        if target:
            from ..contracts.session import Target

            if isinstance(target, Target):
                target_str = target.value
                meta["target"] = target.model_dump()
            elif isinstance(target, dict) and "value" in target:
                target_str = target["value"]
                meta["target"] = target
            else:
                target_str = target

        meta_str = json.dumps(meta)

        with self.store._get_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (id, mode, target, autonomy, created_at, updated_at, status, metadata, memory_namespace) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    sid,
                    mode,
                    target_str,
                    autonomy,
                    now.isoformat(),
                    now.isoformat(),
                    status,
                    meta_str,
                    memory_namespace,
                ),
            )
            conn.commit()

        return Session(
            id=sid,
            mode=mode,
            target=target_str,
            autonomy=autonomy,
            created_at=now,
            updated_at=now,
            status=status,
            metadata=meta,
            memory_namespace=memory_namespace,
        )

    def load(self, session_id: str) -> Session | None:
        with self.store._get_connection() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            if row:
                now = datetime.now()
                conn.execute(
                    "UPDATE sessions SET updated_at = ? WHERE id = ?", (now.isoformat(), session_id)
                )
                conn.commit()

                try:
                    meta = json.loads(row["metadata"]) if row["metadata"] else {}
                except Exception:
                    meta = {}

                return Session(
                    id=row["id"],
                    mode=row["mode"],
                    target=row["target"],
                    autonomy=row["autonomy"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=now,
                    status=row["status"],
                    metadata=meta,
                    memory_namespace=row["memory_namespace"],
                )
        return None

    def save(self, session: Session) -> None:
        now = datetime.now()
        session.updated_at = now
        meta_str = json.dumps(session.metadata)
        with self.store._get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET mode = ?, target = ?, autonomy = ?, updated_at = ?, status = ?, metadata = ?, memory_namespace = ? WHERE id = ?",
                (
                    session.mode,
                    session.target,
                    session.autonomy,
                    now.isoformat(),
                    session.status,
                    meta_str,
                    session.memory_namespace,
                    session.id,
                ),
            )
            conn.commit()

    def set_target(self, session_id: str, new_target: str | None) -> None:
        session = self.load(session_id)
        if session:
            from ..contracts.session import Target

            if isinstance(new_target, Target):
                session.target = new_target.value
                session.metadata["target"] = new_target.model_dump()
            elif isinstance(new_target, dict) and "value" in new_target:
                session.target = new_target["value"]
                session.metadata["target"] = new_target
            else:
                session.target = new_target
            self.save(session)

    def archive(self, session_id: str) -> None:
        session = self.load(session_id)
        if session:
            session.status = "archived"
            self.save(session)

    def list(self, status: str | None = None) -> list[dict[str, Any]]:
        with self.store._get_connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM sessions WHERE status = ? ORDER BY updated_at DESC", (status,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()

            results = []
            for r in rows:
                d = dict(r)
                try:
                    d["metadata"] = json.loads(d["metadata"]) if d["metadata"] else {}
                except Exception:
                    d["metadata"] = {}
                results.append(d)
            return results

    def list_sessions(self) -> builtins.list[dict[str, Any]]:
        return self.list()

    def delete(self, session_id: str) -> None:
        with self.store._get_connection() as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()


# Maintain class names for compatibility
SessionManager = SessionService


class TargetStateMachine:
    """Manages the current state machine of the testing target."""

    def __init__(self):
        self._state = TargetState(target=None, changed=False)

    def set(self, target_str: str) -> TargetState:
        self._state.target = target_str
        self._state.changed = True
        return self._state

    def get(self) -> TargetState | None:
        return self._state

    def change(self, new_target: str) -> None:
        pass

    def validate(self, target_str: str) -> bool:
        return True


class EventBus:
    """Minimal Event Bus for session events."""

    pass

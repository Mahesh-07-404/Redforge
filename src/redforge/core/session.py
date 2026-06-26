"""Session management service for RedForge."""

import uuid
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..contracts.session import SessionState, TargetState

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
                    status TEXT
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


class SessionService:
    """Core Session Service for creating, loading, updating, and listing agent sessions."""
    def __init__(self, store: SessionStore):
        self.store = store

    def create(self, mode: str, target: str | None, autonomy: str, session_id: Optional[str] = None) -> SessionState:
        sid = session_id or str(uuid.uuid4())
        now = datetime.now()
        status = "active"
        
        with self.store._get_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (id, mode, target, autonomy, created_at, updated_at, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (sid, mode, target, autonomy, now.isoformat(), now.isoformat(), status)
            )
            conn.commit()
            
        return SessionState(
            id=sid, mode=mode, target=target, autonomy=autonomy, 
            created_at=now, updated_at=now, status=status
        )

    def load(self, session_id: str) -> SessionState | None:
        with self.store._get_connection() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            if row:
                now = datetime.now()
                conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now.isoformat(), session_id))
                conn.commit()
                return SessionState(
                    id=row["id"], mode=row["mode"], target=row["target"], autonomy=row["autonomy"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=now, status=row["status"]
                )
        return None

    def save(self, session_state: SessionState) -> None:
        now = datetime.now()
        session_state.updated_at = now
        with self.store._get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET mode = ?, target = ?, autonomy = ?, updated_at = ?, status = ? WHERE id = ?",
                (session_state.mode, session_state.target, session_state.autonomy, now.isoformat(), session_state.status, session_state.id)
            )
            conn.commit()

    def set_target(self, session_id: str, new_target: str | None) -> None:
        state = self.load(session_id)
        if state:
            state.target = new_target
            self.save(state)

    def list_sessions(self) -> List[Dict[str, Any]]:
        with self.store._get_connection() as conn:
            rows = conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()
            return [dict(r) for r in rows]

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

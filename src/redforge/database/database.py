"""SQLite-based persistence for RedForge sessions, messages, findings, and tasks."""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseService:
    """Manages SQLite database for session tracking, message history, findings, and tasks."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_path = str(Path.cwd() / "workspaces" / "redforge.db")
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        try:
            with self._get_connection() as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_accessed TEXT NOT NULL,
                        target TEXT,
                        mode TEXT,
                        autonomy TEXT,
                        model TEXT
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        tool_name TEXT,
                        command TEXT,
                        severity TEXT,
                        status TEXT,
                        duration_s REAL,
                        timestamp REAL,
                        FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS findings (
                        id TEXT PRIMARY KEY,
                        session_id TEXT,
                        type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        target TEXT,
                        evidence TEXT, -- JSON-serialized
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        session_id TEXT,
                        description TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        completed_at TEXT,
                        FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                    );
                """)
                logger.info("Database initialized successfully at %s", self.db_path)
        except Exception as exc:
            logger.exception("Failed to initialize database: %s", exc)

    def create_session(
        self,
        session_id: str,
        name: str,
        mode: str = "bugbounty",
        autonomy: str = "manual",
        model: str = "",
        target: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new session in SQLite."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions (id, name, created_at, last_accessed, target, mode, autonomy, model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, name, now, now, target, mode, autonomy, model)
            )
        return {
            "id": session_id,
            "name": name,
            "created_at": now,
            "last_accessed": now,
            "target": target,
            "mode": mode,
            "autonomy": autonomy,
            "model": model
        }

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session metadata and update last accessed timestamp."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            if row:
                conn.execute("UPDATE sessions SET last_accessed = ? WHERE id = ?", (now, session_id))
                return dict(row)
        return None

    def save_session(
        self,
        session_id: str,
        name: str,
        mode: str,
        autonomy: str,
        model: str,
        target: Optional[str]
    ) -> None:
        """Update/save details for an existing session."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET name = ?, mode = ?, autonomy = ?, model = ?, target = ?, last_accessed = ?
                WHERE id = ?
                """,
                (name, mode, autonomy, model, target, now, session_id)
            )

    def delete_session(self, session_id: str) -> bool:
        """Delete session and all related cascade data."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            return cursor.rowcount > 0

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all tracked sessions ordered by last accessed."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM sessions ORDER BY last_accessed DESC").fetchall()
            return [dict(r) for r in rows]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_name: str = "",
        command: str = "",
        severity: str = "",
        status: str = "",
        duration_s: float = 0.0,
        timestamp: Optional[float] = None
    ) -> None:
        """Add a message exchange row."""
        if timestamp is None:
            import time
            timestamp = time.time()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO messages (session_id, role, content, tool_name, command, severity, status, duration_s, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, role, content, tool_name, command, severity, status, duration_s, timestamp)
            )

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all messages for a session ordered by creation."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC",
                (session_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def add_finding(
        self,
        session_id: str,
        id: str,
        type: str,
        title: str,
        description: str,
        severity: str,
        target: str = "",
        evidence: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ) -> None:
        """Add a security finding."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        ev_str = json.dumps(evidence) if evidence is not None else "{}"
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO findings (id, session_id, type, title, description, severity, target, evidence, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (id, session_id, type, title, description, severity, target, ev_str, timestamp)
            )

    def get_findings(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all findings for a session."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM findings WHERE session_id = ? ORDER BY timestamp DESC",
                (session_id,)
            ).fetchall()
            res = []
            for r in rows:
                d = dict(r)
                try:
                    d["evidence"] = json.loads(d["evidence"])
                except Exception:
                    d["evidence"] = {}
                res.append(d)
            return res

    def add_task(
        self,
        session_id: str,
        id: str,
        description: str,
        status: str,
        created_at: Optional[str] = None
    ) -> None:
        """Add a task tracking entry."""
        if created_at is None:
            created_at = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tasks (id, session_id, description, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (id, session_id, description, status, created_at)
            )

    def update_task(
        self,
        session_id: str,
        id: str,
        status: str,
        completed_at: Optional[str] = None
    ) -> None:
        """Update a task's status."""
        with self._get_connection() as conn:
            if completed_at:
                conn.execute(
                    "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ? AND session_id = ?",
                    (status, completed_at, id, session_id)
                )
            else:
                conn.execute(
                    "UPDATE tasks SET status = ? WHERE id = ? AND session_id = ?",
                    (status, id, session_id)
                )

    def get_tasks(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all tasks for a session."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def clear_session_data(self, session_id: str) -> None:
        """Remove all findings, messages, and tasks related to a session without deleting session metadata."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM findings WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM tasks WHERE session_id = ?", (session_id,))


# Keep SessionDatabase alias for backward compatibility during migration
SessionDatabase = DatabaseService

from .store import SessionStore
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from ..contracts.session import SessionState, TargetState

class SessionManager:
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

    def set_target(self, session_id: str, new_target: str) -> None:
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

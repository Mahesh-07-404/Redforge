"""RedForge Session Manager"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from redforge.memory.memory_manager import MemoryManager

class SessionManager:
    """Manages pentesting sessions, ensuring they survive restarts via SQLite"""

    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.db_path = memory_manager.db_path

    def save_session(self, name: str, state: Dict[str, Any]) -> None:
        """Save session state to SQLite"""
        target = state.get("target")
        state_json = json.dumps(state)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO sessions (name, target, state_json) VALUES (?, ?, ?)",
                (name, target, state_json)
            )
            conn.commit()

    def load_session(self, name: str) -> Optional[Dict[str, Any]]:
        """Load session state from SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state_json FROM sessions WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                state = json.loads(row[0])
                # Restore workspace
                self.memory_manager.workspace["target"] = state.get("target")
                self.memory_manager.workspace["findings"] = state.get("findings", [])
                self.memory_manager.workspace["notes"] = state.get("notes", [])
                return state
        return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all saved sessions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT name, target, updated_at FROM sessions")
            return [dict(row) for row in cursor.fetchall()]

    def delete_session(self, name: str) -> bool:
        """Delete a saved session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE name = ?", (name,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

    def export_session(self, name: str, export_path: str) -> bool:
        """Export session JSON to a file"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state_json FROM sessions WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                # Ensure output directory exists
                dest = Path(export_path)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(row[0], encoding="utf-8")
                return True
        return False

    def handle_command(self, cmd_str: str) -> str:
        """
        Handle CLI session commands:
        /session list
        /session save <name>
        /session load <name>
        /session delete <name>
        /session export <name> <file_path>
        """
        parts = cmd_str.strip().split()
        if len(parts) < 2 or parts[0] != "/session":
            return "Invalid session command. Use: /session list, /session save <name>, /session load <name>, etc."

        action = parts[1].lower()

        if action == "list":
            sessions = self.list_sessions()
            if not sessions:
                return "No active or saved sessions."
            lines = ["Saved Sessions:"]
            for s in sessions:
                lines.append(f"- {s['name']} (target: {s['target']}, updated: {s['updated_at']})")
            return "\n".join(lines)

        elif action == "save":
            if len(parts) < 3:
                return "Error: Specify a session name to save (e.g. /session save mysession)."
            name = parts[2]
            state = {
                "target": self.memory_manager.workspace.get("target"),
                "findings": self.memory_manager.workspace.get("findings", []),
                "notes": self.memory_manager.workspace.get("notes", [])
            }
            self.save_session(name, state)
            return f"Session '{name}' saved successfully."

        elif action == "load":
            if len(parts) < 3:
                return "Error: Specify a session name to load."
            name = parts[2]
            state = self.load_session(name)
            if state:
                return f"Session '{name}' loaded successfully. Active target: {state.get('target')}"
            return f"Error: Session '{name}' not found."

        elif action == "delete":
            if len(parts) < 3:
                return "Error: Specify a session name to delete."
            name = parts[2]
            if self.delete_session(name):
                return f"Session '{name}' deleted successfully."
            return f"Error: Session '{name}' not found."

        elif action == "export":
            if len(parts) < 4:
                return "Error: Specify session name and file path (e.g. /session export mysession ./export.json)."
            name = parts[2]
            path = parts[3]
            if self.export_session(name, path):
                return f"Session '{name}' exported successfully to {path}."
            return f"Error: Session '{name}' not found."

        return f"Unknown session action: {action}. Available: list, save, load, delete, export."

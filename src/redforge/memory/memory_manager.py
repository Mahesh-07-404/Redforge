"""RedForge Memory Manager"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

class MemoryManager:
    """Three-layered memory management using SQLite for long-term persistence"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Create a local redforge.db in workspace directory
            self.db_path = Path("./redforge.db")
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

        # Short term in-memory layer (e.g. current loop vars)
        self.short_term: Dict[str, Any] = {}
        # Workspace layer (current session target / findings runtime cache)
        self.workspace: Dict[str, Any] = {
            "target": None,
            "findings": [],
            "notes": []
        }

    def _init_db(self) -> None:
        """Initialize SQLite database tables for long term storage"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Targets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host TEXT UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Findings table
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
            # Reports table
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
            # Notes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Sessions table
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
                (host, description)
            )
            conn.commit()

    def get_targets(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM targets")
            return [dict(row) for row in cursor.fetchall()]

    # Findings
    def add_finding(self, finding: Dict[str, Any]) -> None:
        # Check if already present in workspace findings list
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
                    finding.get("timestamp")
                )
            )
            conn.commit()

    def get_findings(self, verified_only: bool = False) -> List[Dict[str, Any]]:
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
                except Exception:
                    pass
                findings.append(f)
            return findings

    # Reports
    def save_report(self, title: str, target: str, content: str, report_format: str = "md") -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reports (title, target, content, format) VALUES (?, ?, ?, ?)",
                (title, target, content, report_format)
            )
            conn.commit()

    # Notes
    def add_note(self, content: str) -> None:
        self.workspace["notes"].append(content)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO notes (content) VALUES (?)", (content,))
            conn.commit()

    def get_notes(self) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM notes")
            return [row[0] for row in cursor.fetchall()]

    # Workspace management
    def clear_workspace(self) -> None:
        self.workspace = {
            "target": None,
            "findings": [],
            "notes": []
        }

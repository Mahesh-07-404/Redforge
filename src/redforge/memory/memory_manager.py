"""Workspace memory system with RAG support"""

import json
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from redforge.memory.vector import (
    VectorStore, 
    MemoryEntry, 
    SearchResult, 
    create_vector_store
)


@dataclass
class WorkspaceMemory:
    """Memory context for a workspace"""
    workspace_id: str
    session_history: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    context_summary: str = ""


class WorkspaceMemoryManager:
    """Manages workspace memory with RAG capabilities"""
    
    def __init__(
        self,
        workspace_id: str,
        persist_dir: str = "./workspaces",
        vector_db: str = "simple"
    ):
        self.workspace_id = workspace_id
        self.persist_dir = Path(persist_dir) / workspace_id
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.memory_file = self.persist_dir / "memory.json"
        
        self.vector_store = create_vector_store(
            vector_db=vector_db,
            persist_dir=str(self.persist_dir),
            collection_name=f"workspace_{workspace_id[:8]}"
        )
        
        self._memory = WorkspaceMemory(workspace_id=workspace_id)
        self._load()
    
    def _load(self) -> None:
        """Load memory from disk"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r") as f:
                    data = json.load(f)
                    self._memory = WorkspaceMemory(
                        workspace_id=data.get("workspace_id", self.workspace_id),
                        session_history=data.get("session_history", []),
                        findings=data.get("findings", []),
                        notes=data.get("notes", []),
                        context_summary=data.get("context_summary", "")
                    )
            except:
                pass
    
    def _save(self) -> None:
        """Save memory to disk"""
        with open(self.memory_file, "w") as f:
            json.dump({
                "workspace_id": self._memory.workspace_id,
                "session_history": self._memory.session_history,
                "findings": self._memory.findings,
                "notes": self._memory.notes,
                "context_summary": self._memory.context_summary
            }, f, indent=2)
    
    def add_session(self, user_input: str, response: str, metadata: Optional[Dict] = None) -> str:
        """Add a session exchange to memory"""
        session_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "response": response,
            "metadata": metadata or {}
        }
        
        self._memory.session_history.append(session_entry)
        
        entry = MemoryEntry(
            id=session_entry["id"],
            content=f"User: {user_input}\nAssistant: {response}",
            metadata={
                "type": "session",
                "workspace_id": self.workspace_id,
                "timestamp": session_entry["timestamp"]
            },
            workspace_id=self.workspace_id,
            entry_type="session"
        )
        self.vector_store.add([entry])
        
        self._save()
        return session_entry["id"]
    
    def add_finding(
        self,
        finding_type: str,
        title: str,
        description: str,
        severity: str = "medium",
        target: str = "",
        evidence: Optional[Dict] = None
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
            "evidence": evidence or {}
        }
        
        self._memory.findings.append(finding)
        
        entry = MemoryEntry(
            id=finding_id,
            content=f"Finding: {title}\nType: {finding_type}\nSeverity: {severity}\n{description}",
            metadata={
                "type": "finding",
                "finding_type": finding_type,
                "severity": severity,
                "workspace_id": self.workspace_id
            },
            workspace_id=self.workspace_id,
            entry_type="finding"
        )
        self.vector_store.add([entry])
        
        self._save()
        return finding_id
    
    def add_note(self, note: str) -> str:
        """Add a note to memory"""
        note_id = str(uuid.uuid4())
        self._memory.notes.append(note)
        
        entry = MemoryEntry(
            id=note_id,
            content=f"Note: {note}",
            metadata={
                "type": "note",
                "workspace_id": self.workspace_id
            },
            workspace_id=self.workspace_id,
            entry_type="note"
        )
        self.vector_store.add([entry])
        
        self._save()
        return note_id
    
    def update_context_summary(self, summary: str) -> None:
        """Update the workspace context summary"""
        self._memory.context_summary = summary
        self._save()
    
    def search(
        self,
        query: str,
        limit: int = 5,
        entry_type: Optional[str] = None
    ) -> List[SearchResult]:
        """Search workspace memory"""
        filter_dict = {"workspace_id": self.workspace_id}
        if entry_type:
            filter_dict["type"] = entry_type
        
        return self.vector_store.search(query, limit=limit, filter_dict=filter_dict)
    
    def get_context_for_llm(
        self,
        query: str = "",
        max_entries: int = 10
    ) -> str:
        """Get context for LLM with RAG"""
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
                context_parts.append(
                    f"- [{finding['severity'].upper()}] {finding['title']}"
                )
        
        return "\n".join(context_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "workspace_id": self.workspace_id,
            "total_sessions": len(self._memory.session_history),
            "total_findings": len(self._memory.findings),
            "total_notes": len(self._memory.notes),
            "has_summary": bool(self._memory.context_summary),
            "vector_store_available": self.vector_store.is_available,
            "indexed_entries": len(self.vector_store.list_entries())
        }
    
    def list_findings(
        self,
        severity: Optional[str] = None,
        finding_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List findings with optional filtering"""
        findings = self._memory.findings
        
        if severity:
            findings = [f for f in findings if f.get("severity") == severity]
        
        if finding_type:
            findings = [f for f in findings if f.get("type") == finding_type]
        
        return sorted(findings, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent sessions"""
        return sorted(
            self._memory.session_history,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:limit]
    
    def clear(self) -> None:
        """Clear all memory"""
        self._memory = WorkspaceMemory(workspace_id=self.workspace_id)
        self.vector_store.clear()
        self._save()


class GlobalMemory:
    """Global memory manager for all workspaces"""
    
    def __init__(
        self,
        persist_dir: str = "./workspaces",
        vector_db: str = "simple"
    ):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db = vector_db
        
        self.global_store = create_vector_store(
            vector_db=vector_db,
            persist_dir=str(self.persist_dir),
            collection_name="redforge_global"
        )
    
    def add_global_memory(
        self,
        content: str,
        memory_type: str = "general",
        tags: Optional[List[str]] = None
    ) -> str:
        """Add globally accessible memory"""
        memory_id = str(uuid.uuid4())
        
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            metadata={
                "type": memory_type,
                "tags": tags or [],
                "global": True
            },
            entry_type=memory_type
        )
        
        self.global_store.add([entry])
        return memory_id
    
    def search_global(self, query: str, limit: int = 5) -> List[SearchResult]:
        """Search global memory"""
        return self.global_store.search(query, limit=limit)
    
    def get_context(self, query: str = "") -> str:
        """Get global context for LLM"""
        context_parts = []
        
        context_parts.append("## Global Knowledge Base")
        
        if query:
            results = self.search_global(query, limit=10)
            if results:
                context_parts.append(f"\n### Relevant Knowledge (for: {query})")
                for result in results:
                    context_parts.append(f"- {result.content[:200]}...")
        
        return "\n".join(context_parts)

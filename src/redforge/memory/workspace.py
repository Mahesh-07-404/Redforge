"""Workspace management system"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict, field


@dataclass
class Workspace:
    """Workspace model"""
    id: str
    name: str
    created_at: datetime
    last_accessed: datetime
    mode: str = "bugbounty"
    scope: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "mode": self.mode,
            "scope": self.scope,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workspace":
        return cls(
            id=data["id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            mode=data.get("mode", "bugbounty"),
            scope=data.get("scope", []),
            metadata=data.get("metadata", {}),
        )
    
    def to_context(self) -> Dict[str, Any]:
        """Convert to context for agent"""
        return {
            "workspace_id": self.id,
            "workspace_name": self.name,
            "workspace_mode": self.mode,
            "workspace_scope": self.scope,
        }


class WorkspaceManager:
    """Manage workspaces with persistence"""
    
    def __init__(self, persist_dir: str = "./workspaces"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._workspaces_cache: Dict[str, Workspace] = {}
    
    def _get_workspace_dir(self, workspace_id: str) -> Path:
        """Get workspace directory"""
        return self.persist_dir / workspace_id
    
    def _get_metadata_file(self, workspace_id: str) -> Path:
        """Get metadata file path"""
        return self._get_workspace_dir(workspace_id) / "metadata.json"
    
    def _load_metadata(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Load workspace metadata"""
        meta_file = self._get_metadata_file(workspace_id)
        if meta_file.exists():
            with open(meta_file, "r") as f:
                return json.load(f)
        return None
    
    def _save_metadata(self, workspace: Workspace) -> None:
        """Save workspace metadata"""
        ws_dir = self._get_workspace_dir(workspace.id)
        ws_dir.mkdir(parents=True, exist_ok=True)
        
        meta_file = self._get_metadata_file(workspace.id)
        with open(meta_file, "w") as f:
            json.dump(workspace.to_dict(), f, indent=2)
    
    def create_workspace(self, name: str, mode: str = "bugbounty") -> Workspace:
        """Create a new workspace"""
        workspace_id = str(uuid.uuid4())
        now = datetime.now()
        
        workspace = Workspace(
            id=workspace_id,
            name=name,
            created_at=now,
            last_accessed=now,
            mode=mode,
        )
        
        self._save_metadata(workspace)
        self._workspaces_cache[workspace_id] = workspace
        self._create_workspace_dirs(workspace)
        
        return workspace
    
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get workspace by ID"""
        if workspace_id in self._workspaces_cache:
            ws = self._workspaces_cache[workspace_id]
            ws.last_accessed = datetime.now()
            self._save_metadata(ws)
            return ws
        
        data = self._load_metadata(workspace_id)
        if data:
            workspace = Workspace.from_dict(data)
            workspace.last_accessed = datetime.now()
            self._save_metadata(workspace)
            self._workspaces_cache[workspace_id] = workspace
            return workspace
        
        return None
    
    def get_workspace_by_name(self, name: str) -> Optional[Workspace]:
        """Get workspace by name"""
        for ws_dir in self.persist_dir.iterdir():
            if ws_dir.is_dir():
                meta_file = ws_dir / "metadata.json"
                if meta_file.exists():
                    with open(meta_file, "r") as f:
                        data = json.load(f)
                        if data.get("name") == name:
                            return self.get_workspace(data["id"])
        return None
    
    def get_or_create_workspace(self, name: str, mode: str = "bugbounty") -> Workspace:
        """Get existing workspace or create new one"""
        workspace = self.get_workspace_by_name(name)
        if workspace:
            return workspace
        return self.create_workspace(name, mode)
    
    def list_workspaces(self) -> List[Workspace]:
        """List all workspaces"""
        workspaces = []
        
        for ws_dir in self.persist_dir.iterdir():
            if ws_dir.is_dir():
                meta_file = ws_dir / "metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r") as f:
                            data = json.load(f)
                        workspace = Workspace.from_dict(data)
                        workspaces.append(workspace)
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return sorted(workspaces, key=lambda w: w.last_accessed, reverse=True)
    
    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete a workspace"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        import shutil
        ws_dir = self._get_workspace_dir(workspace_id)
        if ws_dir.exists():
            shutil.rmtree(ws_dir)
        
        if workspace_id in self._workspaces_cache:
            del self._workspaces_cache[workspace_id]
        
        return True
    
    def update_workspace(self, workspace: Workspace) -> Workspace:
        """Update workspace"""
        workspace.last_accessed = datetime.now()
        self._save_metadata(workspace)
        self._workspaces_cache[workspace.id] = workspace
        return workspace
    
    def add_session(self, workspace_id: str, session_data: Dict[str, Any]) -> None:
        """Add a session to workspace"""
        ws_dir = self._get_workspace_dir(workspace_id)
        sessions_dir = ws_dir / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        
        session_id = str(uuid.uuid4())
        session_file = sessions_dir / f"{session_id}.json"
        
        session_data["id"] = session_id
        session_data["created_at"] = datetime.now().isoformat()
        
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)
    
    def get_sessions(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a workspace"""
        sessions_dir = self._get_workspace_dir(workspace_id) / "sessions"
        if not sessions_dir.exists():
            return []
        
        sessions = []
        for session_file in sessions_dir.glob("*.json"):
            with open(session_file, "r") as f:
                sessions.append(json.load(f))
        
        return sorted(sessions, key=lambda s: s.get("created_at", ""), reverse=True)
    
    def add_finding(self, workspace_id: str, finding: Dict[str, Any]) -> str:
        """Add a finding to workspace"""
        ws_dir = self._get_workspace_dir(workspace_id)
        findings_dir = ws_dir / "findings"
        findings_dir.mkdir(parents=True, exist_ok=True)
        
        finding_id = str(uuid.uuid4())
        finding_file = findings_dir / f"{finding_id}.json"
        
        finding["id"] = finding_id
        finding["created_at"] = datetime.now().isoformat()
        
        with open(finding_file, "w") as f:
            json.dump(finding, f, indent=2)
        
        return finding_id
    
    def get_findings(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get all findings for a workspace"""
        findings_dir = self._get_workspace_dir(workspace_id) / "findings"
        if not findings_dir.exists():
            return []
        
        findings = []
        for finding_file in findings_dir.glob("*.json"):
            with open(finding_file, "r") as f:
                findings.append(json.load(f))
        
        return sorted(findings, key=lambda f: f.get("created_at", ""), reverse=True)
    
    def _create_workspace_dirs(self, workspace: Workspace) -> None:
        """Create workspace subdirectories"""
        ws_dir = self._get_workspace_dir(workspace.id)
        ws_dir.mkdir(parents=True, exist_ok=True)
        
        (ws_dir / "sessions").mkdir(exist_ok=True)
        (ws_dir / "findings").mkdir(exist_ok=True)
        (ws_dir / "artifacts").mkdir(exist_ok=True)


WorkspaceService = WorkspaceManager


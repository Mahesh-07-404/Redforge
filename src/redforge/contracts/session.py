from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class TargetType(str, Enum):
    Domain = "domain"
    IP = "ip"
    URL = "url"
    APK = "apk"
    CIDR = "cidr"


class ScopePolicy(BaseModel):
    allowed: list[str] = []
    excluded: list[str] = []


class Target(BaseModel):
    value: str
    type: TargetType
    scope: ScopePolicy


class SessionMode(str, Enum):
    BugBounty = "bugbounty"
    CTF = "ctf"
    Pentest = "pentest"
    Learning = "learning"
    Coding = "coding"
    Android = "android"


class SessionStatus(str, Enum):
    Active = "active"
    Paused = "paused"
    Completed = "completed"
    Archived = "archived"


class TargetState(BaseModel):
    target: str | None
    changed: bool = False


class ModeState(BaseModel):
    mode: str


class Session(BaseModel):
    id: str
    mode: str
    target: str | None
    autonomy: str
    created_at: datetime
    updated_at: datetime
    status: str = "active"
    metadata: dict[str, Any] = {}
    memory_namespace: str | None = None


SessionState = Session

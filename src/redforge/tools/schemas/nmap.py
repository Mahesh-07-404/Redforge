from pydantic import BaseModel
from typing import List, Literal, Optional
from .base import BaseToolOutput

class NmapPort(BaseModel):
    port: int
    protocol: Literal["tcp", "udp"]
    state: Literal["open", "closed", "filtered"]
    service: Optional[str] = None
    version: Optional[str] = None

class NmapHostResult(BaseModel):
    ip: str
    hostname: Optional[str] = None
    state: Literal["up", "down"]
    ports: List[NmapPort]

class NmapScanResult(BaseToolOutput):
    tool_name: str = "nmap"
    hosts: List[NmapHostResult]
    scan_type: str = "syn"
    timing_template: int = 3

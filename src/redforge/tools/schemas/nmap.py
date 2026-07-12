from typing import Literal

from pydantic import BaseModel

from .base import BaseToolOutput


class NmapPort(BaseModel):
    port: int
    protocol: Literal["tcp", "udp"]
    state: Literal["open", "closed", "filtered"]
    service: str | None = None
    version: str | None = None


class NmapHostResult(BaseModel):
    ip: str
    hostname: str | None = None
    state: Literal["up", "down"]
    ports: list[NmapPort]


class NmapScanResult(BaseToolOutput):
    tool_name: str = "nmap"
    hosts: list[NmapHostResult]
    scan_type: str = "syn"
    timing_template: int = 3

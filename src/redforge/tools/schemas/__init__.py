from .base import BaseToolOutput
from .nmap import NmapScanResult, NmapHostResult, NmapPort
from .sqlmap import SqlmapResult, SqlmapVulnerability
from .ffuf import FfufResult, FfufMatch

__all__ = [
    "BaseToolOutput",
    "NmapScanResult", "NmapHostResult", "NmapPort",
    "SqlmapResult", "SqlmapVulnerability",
    "FfufResult", "FfufMatch"
]

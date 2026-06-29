from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class Finding(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    confidence: float
    affected_assets: List[str] = []
    evidence: List[str] = []
    references: List[str] = []
    cve: Optional[str] = None
    cwe: Optional[str] = None
    owasp: Optional[str] = None
    mitre: Optional[str] = None
    cvss: Optional[float] = None
    remediation: Optional[str] = None
    status: str = "open"

class ExecutiveSummary(BaseModel):
    scope: str
    objectives: str
    methodology: str
    key_findings: str
    risk_summary: str
    recommendations: str
    conclusion: str

class RiskScore(BaseModel):
    overall_risk: str
    technical_risk: float
    business_risk: float
    likelihood: float
    impact: float
    exploitability: float

class SynthesisReport(BaseModel):
    session_id: str
    execution_id: str
    target: str
    executive_summary: ExecutiveSummary
    findings: List[Finding] = []
    timeline: List[str] = []

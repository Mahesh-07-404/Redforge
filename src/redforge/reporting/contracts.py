from pydantic import BaseModel


class Finding(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    confidence: float
    affected_assets: list[str] = []
    evidence: list[str] = []
    references: list[str] = []
    cve: str | None = None
    cwe: str | None = None
    owasp: str | None = None
    mitre: str | None = None
    cvss: float | None = None
    remediation: str | None = None
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
    findings: list[Finding] = []
    timeline: list[str] = []

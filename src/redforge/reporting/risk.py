from .contracts import RiskScore
from .severity import Severity

class RiskEngine:
    @staticmethod
    def calculate_risk(likelihood: float, impact: float, exploitability: float, confidence: float) -> RiskScore:
        tech_risk = (likelihood + exploitability) / 2.0
        bus_risk = impact
        combined = (tech_risk + bus_risk) / 2.0
        
        if combined >= 8.0:
            overall = Severity.CRITICAL.value
        elif combined >= 6.0:
            overall = Severity.HIGH.value
        elif combined >= 4.0:
            overall = Severity.MEDIUM.value
        elif combined >= 2.0:
            overall = Severity.LOW.value
        else:
            overall = Severity.INFO.value
            
        return RiskScore(
            overall_risk=overall,
            technical_risk=tech_risk,
            business_risk=bus_risk,
            likelihood=likelihood,
            impact=impact,
            exploitability=exploitability
        )

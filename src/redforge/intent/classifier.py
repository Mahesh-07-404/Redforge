from ..contracts.intent import RiskLevel, IntentType

class IntentClassifier:
    def classify(self, intent_type: IntentType) -> RiskLevel:
        mapping = {
            IntentType.SCAN: RiskLevel.MEDIUM,
            IntentType.RECON: RiskLevel.LOW,
            IntentType.EXPLOIT: RiskLevel.HIGH,
            IntentType.REPORT: RiskLevel.SAFE,
            IntentType.LEARN: RiskLevel.SAFE,
            IntentType.CONFIGURE: RiskLevel.LOW,
            IntentType.CLARIFY: RiskLevel.SAFE,
            IntentType.UNKNOWN: RiskLevel.SAFE,
        }
        return mapping.get(intent_type, RiskLevel.SAFE)

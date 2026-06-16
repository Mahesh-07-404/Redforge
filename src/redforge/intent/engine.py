from .parser import IntentParser
from .classifier import IntentClassifier
from .target_watcher import TargetWatcher
from ..contracts.intent import ParsedIntent

class IntentEngine:
    def __init__(self, target_watcher: TargetWatcher):
        self.parser = IntentParser()
        self.classifier = IntentClassifier()
        self.watcher = target_watcher

    def process(self, raw_input: str, current_mode: str, session_id: str, current_autonomy: str) -> ParsedIntent:
        intent = self.parser.parse(raw_input, current_mode, session_id)
        intent.risk_level = self.classifier.classify(intent.intent_type)
        intent = self.watcher.check(intent)
        
        if current_autonomy == "manual":
            intent.requires_approval = True
        elif current_autonomy == "partial" and intent.risk_level in ["high", "destructive"]:
            intent.requires_approval = True
        else:
            intent.requires_approval = False
            
        return intent

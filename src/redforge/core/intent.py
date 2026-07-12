"""Intent analysis service for RedForge."""

import re
from abc import ABC, abstractmethod

from ..contracts.intent import IntentType, ParsedIntent, RiskLevel
from .session import EventBus, TargetStateMachine


class IntentClassificationStrategy(ABC):
    @abstractmethod
    def classify(self, raw_input: str) -> IntentType | None:
        pass


class GeneralChatStrategy(IntentClassificationStrategy):
    GREETINGS = {
        "hi",
        "hello",
        "hey",
        "yo",
        "how are you",
        "thanks",
        "thank you",
        "good morning",
        "good afternoon",
        "good evening",
        "greetings",
    }

    def classify(self, raw_input: str) -> IntentType | None:
        text = raw_input.lower().strip()
        words = re.findall(r"\b\w+\b", text)
        if any(w in self.GREETINGS for w in words) or text in self.GREETINGS:
            return IntentType.GENERAL_CHAT
        if "how are you" in text or "what's up" in text:
            return IntentType.GENERAL_CHAT
        return None


class SessionStrategy(IntentClassificationStrategy):
    SESSION_KEYWORDS = {"session", "continue", "load", "yesterday"}

    def classify(self, raw_input: str) -> IntentType | None:
        text = raw_input.lower()
        if any(kw in text for kw in self.SESSION_KEYWORDS):
            return IntentType.SESSION
        return None


class ReportStrategy(IntentClassificationStrategy):
    REPORT_KEYWORDS = {"report", "findings", "cve", "generate"}

    def classify(self, raw_input: str) -> IntentType | None:
        text = raw_input.lower()
        if any(kw in text for kw in self.REPORT_KEYWORDS):
            return IntentType.REPORT
        return None


class HelpStrategy(IntentClassificationStrategy):
    HELP_KEYWORDS = {"help", "commands", "how to use", "usage", "man page"}

    def classify(self, raw_input: str) -> IntentType | None:
        text = raw_input.lower()
        if any(kw in text for kw in self.HELP_KEYWORDS):
            return IntentType.HELP
        return None


class ConfigStrategy(IntentClassificationStrategy):
    CONFIG_KEYWORDS = {"config", "configure", "setting", "setup", "options"}

    def classify(self, raw_input: str) -> IntentType | None:
        text = raw_input.lower()
        if any(kw in text for kw in self.CONFIG_KEYWORDS):
            return IntentType.CONFIG
        return None


class ToolStrategy(IntentClassificationStrategy):
    TOOL_KEYWORDS = {"tool", "run tool", "execute tool"}

    def classify(self, raw_input: str) -> IntentType | None:
        text = raw_input.lower()
        if any(kw in text for kw in self.TOOL_KEYWORDS):
            return IntentType.TOOL
        return None


class LearningStrategy(IntentClassificationStrategy):
    LEARNING_KEYWORDS = {"learn", "how does", "tutorial", "explain", "learning", "study"}

    def classify(self, raw_input: str) -> IntentType | None:
        text = raw_input.lower()
        if any(kw in text for kw in self.LEARNING_KEYWORDS):
            return IntentType.LEARNING
        return None


class SecurityWorkflowStrategy(IntentClassificationStrategy):
    def classify(self, raw_input: str) -> IntentType | None:
        text = raw_input.lower()
        if "bug bounty" in text or "bugbounty" in text or "bounty" in text:
            return IntentType.BUG_BOUNTY
        if "pentest" in text or "penetration" in text:
            return IntentType.PENTEST
        if "ctf" in text or "capture the flag" in text or "challenge" in text:
            return IntentType.CTF
        return None


class LegacyStrategy(IntentClassificationStrategy):
    def classify(self, raw_input: str) -> IntentType | None:
        text = raw_input.lower()
        if "exploit" in text:
            return IntentType.EXPLOIT
        if "scan" in text:
            return IntentType.SCAN
        if "recon" in text:
            return IntentType.RECON
        return None


class IntentParser:
    """Parses user input to extract intent type, risk, and target."""

    def __init__(self, strategies: list[IntentClassificationStrategy] | None = None):
        self.strategies: list[IntentClassificationStrategy]
        if strategies is None:
            self.strategies = [
                GeneralChatStrategy(),
                SessionStrategy(),
                ReportStrategy(),
                HelpStrategy(),
                ConfigStrategy(),
                ToolStrategy(),
                LearningStrategy(),
                SecurityWorkflowStrategy(),
                LegacyStrategy(),
            ]
        else:
            self.strategies = strategies

    def parse(self, raw_input: str, current_mode: str, session_id: str) -> ParsedIntent:
        intent_type = IntentType.UNKNOWN
        for strategy in self.strategies:
            res = strategy.classify(raw_input)
            if res:
                intent_type = res
                break

        # Target extraction
        target = None
        match = re.search(r"(?:https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", raw_input)
        if match:
            target = match.group(1)

        return ParsedIntent(
            raw_input=raw_input,
            intent_type=intent_type,
            risk_level=RiskLevel.SAFE,
            target=target,
            target_changed=False,
            mode=current_mode,
            entities={},
            requires_approval=False,
            session_id=session_id,
        )


class IntentClassifier:
    """Classifies intent types into risk levels."""

    def classify(self, intent_type: IntentType) -> RiskLevel:
        mapping = {
            IntentType.SCAN: RiskLevel.MEDIUM,
            IntentType.RECON: RiskLevel.LOW,
            IntentType.EXPLOIT: RiskLevel.HIGH,
            IntentType.REPORT: RiskLevel.SAFE,
            IntentType.LEARN: RiskLevel.SAFE,
            IntentType.LEARNING: RiskLevel.SAFE,
            IntentType.CONFIGURE: RiskLevel.LOW,
            IntentType.CONFIG: RiskLevel.LOW,
            IntentType.CLARIFY: RiskLevel.SAFE,
            IntentType.GENERAL_CHAT: RiskLevel.SAFE,
            IntentType.BUG_BOUNTY: RiskLevel.MEDIUM,
            IntentType.PENTEST: RiskLevel.HIGH,
            IntentType.CTF: RiskLevel.LOW,
            IntentType.SESSION: RiskLevel.SAFE,
            IntentType.HELP: RiskLevel.SAFE,
            IntentType.TOOL: RiskLevel.SAFE,
            IntentType.UNKNOWN: RiskLevel.SAFE,
        }
        return mapping.get(intent_type, RiskLevel.SAFE)


class TargetWatcher:
    """Monitors if target changes during execution."""

    def __init__(self, state_machine: TargetStateMachine, event_bus: EventBus):
        self.state_machine = state_machine
        self.event_bus = event_bus

    def check(self, intent: ParsedIntent) -> ParsedIntent:
        current_state = self.state_machine.get()
        if current_state is not None and intent.target and (current_state.target != intent.target):
            intent.target_changed = True
            self.state_machine.set(intent.target)
        return intent


class IntentService:
    """Service to process user inputs and extract security intent."""

    def __init__(self, target_watcher: TargetWatcher):
        self.parser = IntentParser()
        self.classifier = IntentClassifier()
        self.watcher = target_watcher

    def process(
        self, raw_input: str, current_mode: str, session_id: str, current_autonomy: str
    ) -> ParsedIntent:
        intent = self.parser.parse(raw_input, current_mode, session_id)
        intent.risk_level = self.classifier.classify(intent.intent_type)
        intent = self.watcher.check(intent)

        # Retrieve the most suitable prompt template automatically
        from redforge.prompt_library.registry import get_prompt_library_registry
        from redforge.prompts.registry import get_prompt_registry

        try:
            registry = get_prompt_registry()
            suitable_prompt = registry.get_suitable_prompt(intent.intent_type.value)
            intent.prompt_id = suitable_prompt.id
        except Exception:
            intent.prompt_id = "reasoning_thought_loop"

        try:
            lib_registry = get_prompt_library_registry()
            suitable_gen_prompt = lib_registry.get_suitable_prompt(intent.intent_type.value)
            intent.general_prompt_id = suitable_gen_prompt.id
        except Exception:
            intent.general_prompt_id = "chat_general_chat"

        if current_autonomy == "manual":
            intent.requires_approval = True
        elif current_autonomy == "partial" and intent.risk_level in [
            "high",
            "destructive",
            RiskLevel.HIGH,
        ]:
            intent.requires_approval = True
        else:
            intent.requires_approval = False

        return intent

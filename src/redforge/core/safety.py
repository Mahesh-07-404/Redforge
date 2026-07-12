"""Safety enforcement and scope validation service for RedForge."""

import ipaddress
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """Safety enforcement levels"""

    OFF = "off"
    WARN = "warn"
    STRICT = "strict"


class ViolationType(Enum):
    """Types of safety violations"""

    SCOPE_VIOLATION = "scope_violation"
    DANGEROUS_COMMAND = "dangerous_command"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_LEAK = "data_leak"
    PRIVACY_VIOLATION = "privacy_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    PROHIBITED_TECHNIQUE = "prohibited_technique"


@dataclass
class SafetyViolation:
    """Represents a safety violation"""

    violation_type: ViolationType
    message: str
    severity: str  # critical, high, medium, low
    details: dict = field(default_factory=dict)
    blocked: bool = False
    command: str | None = None


@dataclass
class ScopeEntry:
    """A scope entry for testing"""

    pattern: str
    entry_type: str  # domain, ip, subdomain, url
    allowed: bool = True

    def matches(self, target: str) -> bool:
        """Check if target matches this scope entry"""
        if self.entry_type == "domain":
            return target == self.pattern or target.endswith(f".{self.pattern}")
        elif self.entry_type == "subdomain":
            return re.match(self.pattern.replace("*", ".*"), target) is not None
        elif self.entry_type == "ip":
            return self._matches_ip(target)
        elif self.entry_type == "url":
            return target.startswith(self.pattern)
        return False

    def _matches_ip(self, target: str) -> bool:
        """Check IP range matching"""
        try:
            if "/" in self.pattern:
                network = ipaddress.ip_network(self.pattern, strict=False)
                ip = ipaddress.ip_address(target)
                return ip in network
            return target == self.pattern
        except ValueError:
            return False


@dataclass
class Scope:
    """Testing scope definition"""

    entries: list[ScopeEntry] = field(default_factory=list)
    excluded: list[ScopeEntry] = field(default_factory=list)

    def add(self, pattern: str, entry_type: str = "domain"):
        """Add entry to scope"""
        entry = ScopeEntry(pattern=pattern, entry_type=entry_type)
        self.entries.append(entry)

    def exclude(self, pattern: str, entry_type: str = "domain"):
        """Exclude from scope"""
        entry = ScopeEntry(pattern=pattern, entry_type=entry_type, allowed=False)
        self.excluded.append(entry)

    def is_allowed(self, target: str) -> bool:
        """Check if target is within scope"""
        # Check exclusions first
        for ex in self.excluded:
            if ex.matches(target):
                return False

        # Check inclusions
        for entry in self.entries:
            if entry.matches(target):
                return True

        return False


class DangerousCommands:
    """Patterns for dangerous commands"""

    DANGEROUS_PATTERNS = [
        # Data destruction
        (r"rm\s+-rf\s+/(?:\*)?", "Root directory deletion attempt"),
        (r"rm\s+-rf\s+/var", "System directory deletion"),
        (r"rm\s+-rf\s+/etc", "Config directory deletion"),
        (r":\(\)\{\s*:\|:", "Fork bomb"),
        (r"dd\s+if=.*of=/dev/(?:sd|sd|vd|nvme)", "Disk overwrite attempt"),
        # Privilege escalation (destructive)
        (r"chmod\s+777\s+/etc", "Permission escalation on system dir"),
        (r"chown\s+-R\s+\d+:\d+\s+/etc", "Ownership change on system dir"),
        # Network attacks
        (r"hping3", "Hping3 network tool"),
        (r"nmap\s+--script\s+.*dos", "DoS script detected"),
        (r"thc-\w+", "THC toolkit detected"),
        # Payload execution
        (r"eval\s+\$", "Eval with variable"),
        (r"exec\s+.*\$\{", "Exec with variable expansion"),
        # Backdoor installation
        (r"wget.*\|.*sh", "Remote script download and execute"),
        (r"curl.*\|.*sh", "Remote script download and execute"),
        (r"nc\s+-e\s+", "Netcat reverse shell"),
        (r"bash\s+-i.*>/dev/tcp", "Bash reverse shell"),
    ]

    PROHIBITED_COMMANDS = [
        "mkfs",
        "dd if=/dev/zero",
        "shred",
        "killall -9",
        "pkill -9",
    ]


class SafetyService:
    """
    Core safety engine for RedForge
    Enforces ethical boundaries and scope compliance
    """

    def __init__(self, config_path: Path | None = None):
        self.level = SafetyLevel.WARN
        self.scope = Scope()
        self.violations: list[SafetyViolation] = []
        self.dangerous_patterns = DangerousCommands.DANGEROUS_PATTERNS
        self.rate_limits: dict = {}
        self.request_counts: dict = {}

        if config_path and config_path.exists():
            self.load_config(config_path)

    def load_config(self, config_path: Path):
        """Load safety configuration"""
        with open(config_path) as f:
            config = yaml.safe_load(f)

        safety_config = config.get("safety", {})
        self.level = SafetyLevel(safety_config.get("level", "warn"))

        # Load scope
        for domain in safety_config.get("scope", {}).get("domains", []):
            self.scope.add(domain, "domain")

        for ip_range in safety_config.get("scope", {}).get("ip_ranges", []):
            self.scope.add(ip_range, "ip")

        for subdomain in safety_config.get("scope", {}).get("subdomains", []):
            self.scope.add(subdomain, "subdomain")

        for url in safety_config.get("scope", {}).get("urls", []):
            self.scope.add(url, "url")

        for exclusion in safety_config.get("scope", {}).get("excluded", []):
            self.scope.exclude(exclusion)

        logger.info(f"Safety config loaded: level={self.level.value}")

    def check_target(self, target: str) -> SafetyViolation | None:
        """Check if target is within scope"""
        if not self.scope.is_allowed(target):
            return SafetyViolation(
                violation_type=ViolationType.SCOPE_VIOLATION,
                message=f"Target '{target}' is outside authorized scope",
                severity="critical",
                blocked=self.level == SafetyLevel.STRICT,
                details={"target": target},
            )
        return None

    def check_command(self, command: str) -> SafetyViolation | None:
        """Check if command is dangerous"""
        # Check pattern matches
        for pattern, description in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return SafetyViolation(
                    violation_type=ViolationType.DANGEROUS_COMMAND,
                    message=f"Dangerous command detected: {description}",
                    severity="high",
                    blocked=True,
                    command=command,
                    details={"pattern": pattern, "description": description},
                )

        # Check prohibited commands
        for prohibited in DangerousCommands.PROHIBITED_COMMANDS:
            if prohibited in command:
                return SafetyViolation(
                    violation_type=ViolationType.DANGEROUS_COMMAND,
                    message=f"Prohibited command: {prohibited}",
                    severity="critical",
                    blocked=True,
                    command=command,
                )

        return None

    def check_rate_limit(
        self, endpoint: str, limit: int = 100, window: int = 60
    ) -> SafetyViolation | None:
        """Check if rate limit is exceeded"""
        import time

        current = time.time()
        key = f"{endpoint}:{int(current / window)}"

        self.request_counts[key] = self.request_counts.get(key, 0) + 1

        if self.request_counts[key] > limit:
            return SafetyViolation(
                violation_type=ViolationType.RATE_LIMIT_EXCEEDED,
                message=f"Rate limit exceeded for {endpoint}",
                severity="medium",
                blocked=False,
                details={"endpoint": endpoint, "limit": limit, "window": window},
            )

        return None

    def check_data_exposure(
        self, data: str, pii_patterns: list[str | tuple[str, str]] | None = None
    ) -> list[SafetyViolation]:
        """Check for sensitive data exposure"""
        violations = []

        default_patterns = [
            (r"\b\d{3}-\d{2}-\d{4}\b", "SSN detected"),
            (r"\b\d{16}\b", "Credit card number detected"),
            (r"password[=:]\s*\S+", "Password in plain text"),
            (r"api[_-]?key[=:]\s*\S+", "API key detected"),
            (r"sk-[a-zA-Z0-9]{20,}", "Secret key detected"),
        ]

        if pii_patterns:
            patterns = []
            for item in pii_patterns:
                if isinstance(item, tuple):
                    patterns.append(item)
                else:
                    patterns.append((item, "Sensitive data detected"))
        else:
            patterns = default_patterns

        for pattern, description in patterns:
            matches = re.findall(pattern, data, re.IGNORECASE)
            if matches:
                violations.append(
                    SafetyViolation(
                        violation_type=ViolationType.DATA_LEAK,
                        message=f"Potential data exposure: {description}",
                        severity="high",
                        blocked=False,
                        details={"pattern": pattern, "matches": len(matches)},
                    )
                )

        return violations

    def validate_action(
        self,
        action: str,
        target: str | None = None,
        command: str | None = None,
        data: str | None = None,
    ) -> list[SafetyViolation]:
        """Comprehensive action validation"""
        violations = []

        # Check target scope
        if target:
            violation = self.check_target(target)
            if violation:
                violations.append(violation)

        # Check command safety
        if command:
            violation = self.check_command(command)
            if violation:
                violations.append(violation)

        # Check data exposure
        if data:
            violations.extend(self.check_data_exposure(data))

        # Log violations
        for v in violations:
            self.violations.append(v)
            if v.blocked:
                logger.warning(f"BLOCKED: {v.message}")
            else:
                logger.info(f"WARNING: {v.message}")

        return violations

    def is_blocked(self, violations: list[SafetyViolation]) -> bool:
        """Check if any violation should block action"""
        return any(v.blocked for v in violations)

    def get_violations_summary(self) -> dict:
        """Get summary of all violations"""
        summary: dict[str, Any] = {
            "total": len(self.violations),
            "by_type": {},
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "blocked": sum(1 for v in self.violations if v.blocked),
        }

        for v in self.violations:
            vt = v.violation_type.value
            summary["by_type"][vt] = summary["by_type"].get(vt, 0) + 1
            summary["by_severity"][v.severity] += 1

        return summary

    def clear_violations(self):
        """Clear violation history"""
        self.violations.clear()
        self.request_counts.clear()


SafetyEngine = SafetyService


class ProhibitedTechniques:
    """Techniques that are prohibited"""

    PROHIBITED = {
        "ddos": "Denial of Service attacks are prohibited",
        "spam": "Spam generation is prohibited",
        "phishing": "Phishing activities are prohibited",
        "social_engineering": "Social engineering without consent is prohibited",
        "physical_access": "Physical security testing requires explicit permission",
        "deceptive_impact": "Actions that impact users deceptively are prohibited",
    }


class SafetyValidator:
    """Validates actions against safety policies"""

    def __init__(self, safety_engine: SafetyService):
        self.engine = safety_engine

    def validate_bugbounty_action(self, action: dict) -> list[SafetyViolation]:
        """Validate bug bounty specific actions"""
        violations = []

        target = action.get("target")
        technique = action.get("technique", "").lower()

        # Check technique prohibition
        for prohibited, reason in ProhibitedTechniques.PROHIBITED.items():
            if prohibited in technique:
                violations.append(
                    SafetyViolation(
                        violation_type=ViolationType.PROHIBITED_TECHNIQUE,
                        message=reason,
                        severity="critical",
                        blocked=True,
                        details={"technique": technique},
                    )
                )

        # Check target
        if target:
            v = self.engine.check_target(target)
            if v:
                violations.append(v)

        return violations

    def validate_ctf_action(self, action: dict) -> list[SafetyViolation]:
        """Validate CTF specific actions (generally more permissive)"""
        violations = []

        # CTF usually has full scope, but still check dangerous commands
        if action.get("command"):
            v = self.engine.check_command(action["command"])
            if v:
                violations.append(v)

        return violations

    def validate_learning_action(self, action: dict) -> list[SafetyViolation]:
        """Validate learning mode actions (safe sandboxing)"""
        violations = []

        # Learning mode should have strict command checking
        if action.get("command"):
            v = self.engine.check_command(action["command"])
            if v:
                violations.append(v)

        return violations

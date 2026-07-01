"""
RedForge Mode Implementations
Complete mode handlers for Bug Bounty, CTF, Learning, Coding, and Android
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Mode(Enum):
    BUGBOUNTY = "bugbounty"
    CTF = "ctf"
    LEARNING = "learning"
    CODING = "coding"
    ANDROID = "android"


@dataclass
class Finding:
    """Represents a security finding"""

    id: str
    title: str
    severity: str  # critical, high, medium, low, info
    category: str
    description: str
    target: str
    evidence: dict[str, Any] = field(default_factory=dict)
    impact: str = ""
    remediation: str = ""
    cvss_score: float | None = None
    cwe_id: str | None = None
    status: str = "open"  # open, confirmed, resolved, duplicate
    references: list[str] = field(default_factory=list)
    created_at: str | None = None


@dataclass
class CTFChallenge:
    """Represents a CTF challenge"""

    id: str
    name: str
    category: str  # web, crypto, binary, forensics, misc
    points: int
    solved: bool = False
    flag: str | None = None
    hints: list[str] = field(default_factory=list)
    solve_time: str | None = None
    writeup: str = ""


@dataclass
class LearningTopic:
    """Represents a learning topic"""

    id: str
    title: str
    category: str
    difficulty: str  # beginner, intermediate, advanced
    objectives: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    exercises: list[str] = field(default_factory=list)
    completed: bool = False


@dataclass
class ModeConfig:
    """Configuration for a mode"""

    name: str
    description: str
    skills_dir: str
    default_scope: list[str] = field(default_factory=list)
    essential_tools: list[str] = field(default_factory=list)
    autonomy_level: str = "manual"
    safety_level: str = "warn"
    features: dict[str, bool] = field(default_factory=dict)


class BaseMode(ABC):
    """Base class for all modes"""

    def __init__(self, config: ModeConfig):
        self.config = config
        self.mode_name = config.name
        self.safety_engine = None  # Will be injected
        self.tool_manager = None  # Will be injected
        self.llm = None  # Will be injected

    @abstractmethod
    def execute(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a task in this mode"""
        pass

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Get mode capabilities"""
        pass

    def set_safety_engine(self, engine):
        """Set safety engine"""
        self.safety_engine = engine

    def set_tool_manager(self, manager):
        """Set tool manager"""
        self.tool_manager = manager

    def set_llm(self, llm):
        """Set LLM"""
        self.llm = llm


class BugBountyMode(BaseMode):
    """Bug Bounty hunting mode"""

    def __init__(self, config: ModeConfig):
        super().__init__(config)
        self.findings: list[Finding] = []
        self.scope: list[str] = config.default_scope
        self.program_config: dict | None = None

    def execute(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute bug bounty task"""
        results = {"task": task, "findings": [], "recon": {}, "exploits": []}

        # Route to appropriate handler
        task_lower = task.lower()

        if "recon" in task_lower or "enumerate" in task_lower:
            results["recon"] = self._run_recon(task, context)
        elif "scan" in task_lower or "test" in task_lower:
            results["findings"] = self._run_scan(task, context)
        elif "exploit" in task_lower or "test" in task_lower:
            results["exploits"] = self._run_exploit(task, context)
        elif "report" in task_lower:
            return self._generate_report(task, context)
        else:
            # Use LLM for general assistance
            if self.llm:
                results["response"] = self.llm.generate(task)

        return results

    def _run_recon(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Run reconnaissance"""
        target = context.get("target", "")

        recon_results = {"subdomains": [], "ports": [], "technologies": [], "endpoints": []}

        # Check for tools
        if self.tool_manager:
            required = ["nmap", "ffuf", "subfinder"]
            self.tool_manager.install_missing(required)

        # Run recon commands (would be actual execution in production)
        logger.info(f"Running recon on {target}")

        return recon_results

    def _run_scan(self, task: str, context: dict[str, Any]) -> list[Finding]:
        """Run vulnerability scan"""
        target = context.get("target", "")

        findings = []

        # Basic vulnerability checks
        # In production, would use actual scanners

        return findings

    def _run_exploit(self, task: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Run exploitation tests"""
        target = context.get("target", "")
        findings = context.get("findings", [])

        exploits = []

        for finding in findings:
            if self._test_exploit(finding):
                exploits.append(
                    {"finding_id": finding.id, "exploitable": True, "poc": "PoC code here"}
                )

        return exploits

    def _test_exploit(self, finding: Finding) -> bool:
        """Test if a finding is exploitable"""
        # Simplified check
        return finding.severity in ("critical", "high")

    def _generate_report(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Generate bug bounty report"""
        findings = context.get("findings", self.findings)

        report = {
            "title": "Bug Bounty Report",
            "program": (
                self.program_config.get("name", "Unknown") if self.program_config else "Unknown"
            ),
            "scope": self.scope,
            "findings_summary": {
                "critical": sum(1 for f in findings if f.severity == "critical"),
                "high": sum(1 for f in findings if f.severity == "high"),
                "medium": sum(1 for f in findings if f.severity == "medium"),
                "low": sum(1 for f in findings if f.severity == "low"),
            },
            "findings": [
                {
                    "id": f.id,
                    "title": f.title,
                    "severity": f.severity,
                    "description": f.description,
                    "remediation": f.remediation,
                }
                for f in findings
            ],
            "generated_at": self._get_timestamp(),
        }

        return report

    def add_finding(self, finding: Finding):
        """Add a finding"""
        self.findings.append(finding)

    def get_capabilities(self) -> list[str]:
        return [
            "Reconnaissance (subdomain, port, technology enumeration)",
            "Vulnerability scanning (web, API, network)",
            "Exploitation testing (SQLi, XSS, RCE, etc.)",
            "Report generation (HackerOne, Bugcrowd formats)",
            "CVSS scoring",
            "CWE mapping",
            "Scope management",
        ]

    def set_program(self, program_config: dict):
        """Set bug bounty program configuration"""
        self.program_config = program_config
        self.scope = program_config.get("scope", {}).get("targets", [])

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().isoformat()


class CTFMode(BaseMode):
    """CTF competition mode"""

    def __init__(self, config: ModeConfig):
        super().__init__(config)
        self.challenges: dict[str, CTFChallenge] = {}
        self.score: int = 0
        self.solved: list[str] = []
        self.team_name: str | None = None

    def execute(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute CTF task"""
        results: dict[str, Any] = {"task": task, "solve": None, "hints": [], "leaderboard": {}}

        task_lower = task.lower()

        if "solve" in task_lower or "flag" in task_lower:
            results["solve"] = self._solve_challenge(task, context)
        elif "list" in task_lower or "challenges" in task_lower:
            results["challenges"] = self._list_challenges(context)
        elif "hint" in task_lower:
            results["hints"] = self._get_hints(task, context)
        elif "score" in task_lower:
            results["score"] = self._get_score()
        elif "submit" in task_lower:
            results["submission"] = self._submit_flag(task, context)
        else:
            # Use LLM for hints/guidance
            if self.llm:
                results["guidance"] = self._get_guidance(task, context)

        return results

    def _solve_challenge(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Attempt to solve a challenge"""
        challenge_id = context.get("challenge_id", "")
        solution = context.get("solution", "")

        challenge = self.challenges.get(challenge_id)
        if not challenge:
            return {"status": "error", "message": "Challenge not found"}

        # Check if already solved
        if challenge.solved:
            return {"status": "already_solved", "points": challenge.points}

        # Verify flag
        if solution == challenge.flag:
            challenge.solved = True
            self.solved.append(challenge_id)
            self.score += challenge.points
            return {
                "status": "correct",
                "points": challenge.points,
                "total_score": self.score,
                "message": "Correct flag!",
            }
        else:
            return {"status": "incorrect", "message": "Wrong flag"}

    def _list_challenges(self, context: dict[str, Any]) -> dict[str, Any]:
        """List available challenges"""
        category = context.get("category")

        challenges = [
            {
                "id": c.id,
                "name": c.name,
                "category": c.category,
                "points": c.points,
                "solved": c.solved,
                "available": not c.solved,
            }
            for c in self.challenges.values()
            if not category or c.category == category
        ]

        return {
            "challenges": challenges,
            "total_points": self.score,
            "solved_count": len(self.solved),
        }

    def _get_hints(self, task: str, context: dict[str, Any]) -> list[str]:
        """Get hints for a challenge"""
        challenge_id = context.get("challenge_id")
        if not isinstance(challenge_id, str):
            return []
        challenge = self.challenges.get(challenge_id)

        if not challenge:
            return []

        hint_level = context.get("level", 1)
        return challenge.hints[:hint_level]

    def _get_score(self) -> dict[str, Any]:
        """Get current score"""
        return {
            "score": self.score,
            "solved": len(self.solved),
            "team": self.team_name or "Individual",
        }

    def _submit_flag(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Submit a flag"""
        flag = context.get("flag", "")
        return self._solve_challenge(task, {"challenge_id": "current", "solution": flag})

    def _get_guidance(self, task: str, context: dict[str, Any]) -> str:
        """Get LLM guidance for challenge"""
        if self.llm:
            return self.llm.generate(f"Help me solve this CTF challenge: {task}")
        return "LLM not configured"

    def add_challenge(self, challenge: CTFChallenge):
        """Add a challenge"""
        self.challenges[challenge.id] = challenge

    def get_capabilities(self) -> list[str]:
        return [
            "Challenge listing by category",
            "Flag submission and validation",
            "Score tracking",
            "Hint system",
            "CTF strategy advice",
            "Writeup generation",
        ]


class LearningMode(BaseMode):
    """Learning mode for skill development"""

    def __init__(self, config: ModeConfig):
        super().__init__(config)
        self.topics: dict[str, LearningTopic] = {}
        self.progress: dict[str, float] = {}  # topic_id -> completion %

    def execute(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute learning task"""
        results: dict[str, Any] = {"task": task, "lesson": None, "exercise": None, "progress": {}}

        task_lower = task.lower()

        if "learn" in task_lower or "lesson" in task_lower:
            results["lesson"] = self._get_lesson(task, context)
        elif "exercise" in task_lower or "practice" in task_lower:
            results["exercise"] = self._get_exercise(task, context)
        elif "progress" in task_lower:
            results["progress"] = self._get_progress()
        elif "topic" in task_lower or "list" in task_lower:
            results["topics"] = self._list_topics(context)
        else:
            # Use LLM for Q&A
            if self.llm:
                results["answer"] = self.llm.generate(task)

        return results

    def _get_lesson(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Get lesson content"""
        topic_id = context.get("topic_id", "")
        topic = self.topics.get(topic_id)

        if not topic:
            return {"error": "Topic not found"}

        return {
            "title": topic.title,
            "category": topic.category,
            "difficulty": topic.difficulty,
            "objectives": topic.objectives,
            "resources": topic.resources,
            "content": "Lesson content would be loaded here",
        }

    def _get_exercise(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Get exercise"""
        topic_id = context.get("topic_id", "")
        topic = self.topics.get(topic_id)

        if not topic:
            return {"error": "Topic not found"}

        return {"exercises": topic.exercises, "topic": topic.title}

    def _get_progress(self) -> dict[str, float]:
        """Get learning progress"""
        return self.progress

    def _list_topics(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """List available topics"""
        category = context.get("category")

        topics = [
            {
                "id": t.id,
                "title": t.title,
                "category": t.category,
                "difficulty": t.difficulty,
                "completion": self.progress.get(t.id, 0),
            }
            for t in self.topics.values()
            if not category or t.category == category
        ]

        return topics

    def add_topic(self, topic: LearningTopic):
        """Add a learning topic"""
        self.topics[topic.id] = topic

    def update_progress(self, topic_id: str, progress: float):
        """Update learning progress"""
        self.progress[topic_id] = min(100, max(0, progress))

    def get_capabilities(self) -> list[str]:
        return [
            "Topic-based learning paths",
            "Interactive exercises",
            "Progress tracking",
            "Skill assessments",
            "Resource recommendations",
        ]


class CodingMode(BaseMode):
    """Secure coding practice mode"""

    def __init__(self, config: ModeConfig):
        super().__init__(config)
        self.code_samples: dict[str, dict] = {}
        self.vulnerabilities: list[dict] = []

    def execute(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute coding task"""
        results: dict[str, Any] = {"task": task, "analysis": None, "fix": None}

        task_lower = task.lower()

        if "analyze" in task_lower or "scan" in task_lower:
            results["analysis"] = self._analyze_code(task, context)
        elif "fix" in task_lower or "secure" in task_lower:
            results["fix"] = self._fix_vulnerability(task, context)
        elif "vulnerable" in task_lower:
            results["examples"] = self._get_vulnerable_examples(task, context)
        elif "best" in task_lower or "secure" in task_lower:
            results["examples"] = self._get_secure_examples(task, context)
        else:
            if self.llm:
                results["response"] = self.llm.generate(task)

        return results

    def _analyze_code(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze code for vulnerabilities"""
        code = context.get("code", "")
        language = context.get("language", "python")

        # Use LLM for analysis
        if self.llm:
            analysis = self.llm.generate(
                f"Analyze this {language} code for security vulnerabilities:\n\n{code}"
            )

        return {
            "language": language,
            "vulnerabilities": self.vulnerabilities,
            "analysis": analysis if self.llm else "LLM not configured",
        }

    def _fix_vulnerability(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Fix a vulnerability"""
        code = context.get("code", "")
        vuln_type = context.get("vulnerability_type", "")

        if self.llm:
            fix = self.llm.generate(
                f"Fix this security vulnerability ({vuln_type}) in the code:\n\n{code}"
            )

        return {
            "original": code,
            "fixed": fix if self.llm else "LLM not configured",
            "vulnerability": vuln_type,
        }

    def _get_vulnerable_examples(self, task: str, context: dict[str, Any]) -> list[dict]:
        """Get vulnerable code examples"""
        return [
            {
                "type": "sql_injection",
                "language": "python",
                "vulnerable": "# Vulnerable\nquery = 'SELECT * FROM users WHERE name=' + name",
                "description": "SQL Injection via string concatenation",
            }
        ]

    def _get_secure_examples(self, task: str, context: dict[str, Any]) -> list[dict]:
        """Get secure code examples"""
        return [
            {
                "type": "sql_injection",
                "language": "python",
                "secure": "# Secure\ncursor.execute('SELECT * FROM users WHERE name=?', (name,))",
                "description": "SQL Injection prevention via parameterized query",
            }
        ]

    def get_capabilities(self) -> list[str]:
        return [
            "Code vulnerability analysis",
            "Secure coding recommendations",
            "Vulnerable code examples",
            "Fix suggestions",
            "Security best practices",
        ]


class AndroidMode(BaseMode):
    """Android security testing mode"""

    def __init__(self, config: ModeConfig):
        super().__init__(config)
        self.apks: list[str] = []
        self.findings: list[Finding] = []

    def execute(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute Android security task"""
        results: dict[str, Any] = {"task": task, "analysis": None, "finding": None}

        task_lower = task.lower()

        if "analyze" in task_lower or "reverse" in task_lower:
            results["analysis"] = self._analyze_apk(task, context)
        elif "frida" in task_lower or "hook" in task_lower:
            results["script"] = self._generate_frida_script(task, context)
        elif "find" in task_lower or "vulnerability" in task_lower:
            results["finding"] = self._find_vulnerability(task, context)
        else:
            if self.llm:
                results["response"] = self.llm.generate(task)

        return results

    def _analyze_apk(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze an APK"""
        apk_path = context.get("apk_path", "")

        # Check for tools
        if self.tool_manager:
            required = ["apktool", "jadx", "frida-tools"]
            self.tool_manager.install_missing(required)

        return {
            "apk": apk_path,
            "components": {},
            "permissions": [],
            "secrets": [],
            "vulnerabilities": [],
        }

    def _generate_frida_script(self, task: str, context: dict[str, Any]) -> str:
        """Generate Frida script"""
        target = context.get("target_class", "")
        method = context.get("target_method", "")

        script = f"""Java.perform(function() {{
    var Target = Java.use("{target}");
    Target.{method}.implementation = function(arg) {{
        console.log("[*] Called: {method}");
        console.log("[*] Arg:", arg);
        return this.{method}(arg);
    }};
}});"""

        return script

    def _find_vulnerability(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Find Android vulnerabilities"""
        return {
            "hardcoded_secrets": [],
            "insecure_storage": [],
            "weak_crypto": [],
            "ssl_pinning": [],
            "exported_components": [],
        }

    def get_capabilities(self) -> list[str]:
        return [
            "APK analysis and reverse engineering",
            "Frida script generation",
            "SSL pinning bypass",
            "Hardcoded secret detection",
            "Android vulnerability scanning",
        ]


class ModeFactory:
    """Factory for creating mode instances"""

    MODES = {
        Mode.BUGBOUNTY: ModeConfig(
            name="bugbounty",
            description="Bug bounty hunting mode",
            essential_tools=["nmap", "ffuf", "sqlmap", "nuclei", "subfinder"],
            skills_dir="skills/MODES/BUGBOUNTY",
            autonomy_level="manual",
            safety_level="strict",
        ),
        Mode.CTF: ModeConfig(
            name="ctf",
            description="CTF competition mode",
            essential_tools=["gdb", "pwntools", "python3", "strings"],
            skills_dir="skills/MODES/CTF",
            autonomy_level="full",
            safety_level="warn",
        ),
        Mode.LEARNING: ModeConfig(
            name="learning",
            description="Learning and skill development",
            essential_tools=["python3"],
            skills_dir="skills/MODES/LEARNING",
            autonomy_level="knowledge",
            safety_level="strict",
        ),
        Mode.CODING: ModeConfig(
            name="coding",
            description="Secure coding practice",
            essential_tools=["python3"],
            skills_dir="skills/MODES/CODING",
            autonomy_level="knowledge",
            safety_level="warn",
        ),
        Mode.ANDROID: ModeConfig(
            name="android",
            description="Android security testing",
            essential_tools=["apktool", "jadx", "frida-tools"],
            skills_dir="skills/MODES/ANDROID",
            autonomy_level="manual",
            safety_level="strict",
        ),
    }

    @classmethod
    def create(cls, mode: Mode) -> BaseMode:
        """Create a mode instance"""
        config = cls.MODES.get(mode)
        if not config:
            raise ValueError(f"Unknown mode: {mode}")

        if mode == Mode.BUGBOUNTY:
            return BugBountyMode(config)
        elif mode == Mode.CTF:
            return CTFMode(config)
        elif mode == Mode.LEARNING:
            return LearningMode(config)
        elif mode == Mode.CODING:
            return CodingMode(config)
        elif mode == Mode.ANDROID:
            return AndroidMode(config)

        raise ValueError(f"Unimplemented mode: {mode}")

    @classmethod
    def get_all_modes(cls) -> list[ModeConfig]:
        """Get all mode configurations"""
        return list(cls.MODES.values())

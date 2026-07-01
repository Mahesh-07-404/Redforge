from abc import ABC, abstractmethod

from ..contracts.intent import IntentType
from .plan import Plan
from .planner_context import PlannerContext
from .task import Task
from .task_graph import TaskGraph


class PlanningStrategy(ABC):
    @abstractmethod
    def can_handle(self, context: PlannerContext) -> bool:
        pass

    @abstractmethod
    def create_plan(self, context: PlannerContext) -> Plan:
        pass

    def _build_plan_from_graph(
        self, goal: str, graph: TaskGraph, confidence: float = 1.0, warnings: list[str] = []
    ) -> Plan:
        ordered_tasks = graph.get_ordered_tasks()
        dep_graph = {t.id: t.dependencies for t in ordered_tasks}
        estimated_duration = sum(t.estimated_duration for t in ordered_tasks)
        required_tools = list(set(t.tool_hint for t in ordered_tasks if t.tool_hint))
        approval_required = any(t.requires_confirmation for t in ordered_tasks)

        return Plan(
            goal=goal,
            ordered_tasks=ordered_tasks,
            dependency_graph=dep_graph,
            estimated_duration=estimated_duration,
            confidence=confidence,
            warnings=warnings,
            required_tools=required_tools,
            approval_required=approval_required,
        )


class PassiveReconStrategy(PlanningStrategy):
    def can_handle(self, context: PlannerContext) -> bool:
        if not context.intent:
            return False
        raw = context.intent.raw_input.lower()
        return "passive recon" in raw or (
            context.intent.intent_type == IntentType.RECON and "passive" in raw
        )

    def create_plan(self, context: PlannerContext) -> Plan:
        graph = TaskGraph()

        t1 = Task(
            id="dns",
            title="Resolve DNS",
            description="Perform DNS lookup and domain resolution",
            estimated_duration=10,
        )
        t2 = Task(
            id="whois",
            title="WHOIS",
            description="Gather WHOIS registration information",
            estimated_duration=15,
        )
        t3 = Task(
            id="subfinder",
            title="Subfinder",
            description="Enumerate subdomains passively",
            estimated_duration=60,
            tool_hint="subfinder",
        )
        t4 = Task(
            id="httpx",
            title="HTTPX",
            description="Probe active web servers",
            estimated_duration=45,
            dependencies=["subfinder"],
            tool_hint="httpx",
        )
        t5 = Task(
            id="screenshot",
            title="Screenshot",
            description="Capture web UI screenshots",
            estimated_duration=30,
            dependencies=["httpx"],
        )
        t6 = Task(
            id="tech_detect",
            title="Technology Detection",
            description="Identify backend technology stacks",
            estimated_duration=20,
            dependencies=["httpx"],
        )
        t7 = Task(
            id="nuclei",
            title="Nuclei",
            description="Scan for passive CVE indicators",
            estimated_duration=120,
            dependencies=["httpx"],
            tool_hint="nuclei",
        )

        for t in [t1, t2, t3, t4, t5, t6, t7]:
            graph.add_task(t)

        target_val = context.target or (
            context.active_session.target if context.active_session else ""
        )
        return self._build_plan_from_graph(f"Perform passive recon on {target_val}", graph)


class WebEnumerationStrategy(PlanningStrategy):
    def can_handle(self, context: PlannerContext) -> bool:
        if not context.intent:
            return False
        raw = context.intent.raw_input.lower()
        return (
            "web enumeration" in raw
            or "enumerate" in raw
            or context.intent.intent_type == IntentType.SCAN
        )

    def create_plan(self, context: PlannerContext) -> Plan:
        graph = TaskGraph()

        t1 = Task(
            id="portscan",
            title="Port Scan",
            description="Perform TCP port scan",
            estimated_duration=120,
            tool_hint="nmap",
        )
        t2 = Task(
            id="service_discovery",
            title="Service Discovery",
            description="Identify service versions",
            estimated_duration=90,
            dependencies=["portscan"],
            tool_hint="nmap",
        )
        t3 = Task(
            id="dir_brute",
            title="Directory Brute Force",
            description="Search for hidden directory paths",
            estimated_duration=180,
            dependencies=["service_discovery"],
            tool_hint="ffuf",
        )

        for t in [t1, t2, t3]:
            graph.add_task(t)

        target_val = context.target or (
            context.active_session.target if context.active_session else ""
        )
        return self._build_plan_from_graph(f"Web Enumeration on {target_val}", graph)


class BugBountyStrategy(PlanningStrategy):
    def can_handle(self, context: PlannerContext) -> bool:
        if not context.intent:
            return False
        return (
            context.intent.intent_type == IntentType.BUG_BOUNTY
            or "bug bounty" in context.intent.raw_input.lower()
        )

    def create_plan(self, context: PlannerContext) -> Plan:
        graph = TaskGraph()

        t1 = Task(
            id="scope",
            title="Scope Verification",
            description="Verify target is in allowed testing boundaries",
            estimated_duration=5,
        )
        t2 = Task(
            id="passive",
            title="Passive Enumeration",
            description="Run passive reconnaissance",
            estimated_duration=60,
            dependencies=["scope"],
            tool_hint="subfinder",
        )
        t3 = Task(
            id="active_scan",
            title="Active Port Scanning",
            description="Scan active service ports",
            estimated_duration=120,
            dependencies=["scope"],
            tool_hint="nmap",
        )
        t4 = Task(
            id="vuln_assess",
            title="Vulnerability Assessment",
            description="Verify vulnerability vectors",
            estimated_duration=180,
            dependencies=["passive", "active_scan"],
            tool_hint="nuclei",
        )

        for t in [t1, t2, t3, t4]:
            graph.add_task(t)

        target_val = context.target or (
            context.active_session.target if context.active_session else ""
        )
        return self._build_plan_from_graph(f"Generate bug bounty workflow for {target_val}", graph)


class CTFStrategy(PlanningStrategy):
    def can_handle(self, context: PlannerContext) -> bool:
        if not context.intent:
            return False
        return (
            context.intent.intent_type == IntentType.CTF
            or "ctf" in context.intent.raw_input.lower()
        )

    def create_plan(self, context: PlannerContext) -> Plan:
        graph = TaskGraph()

        t1 = Task(
            id="analysis",
            title="Challenge Analysis",
            description="Analyze CTF challenge metadata",
            estimated_duration=10,
        )
        t2 = Task(
            id="re",
            title="Reverse Engineering / Decompilation",
            description="Decompile challenge binaries",
            estimated_duration=300,
            dependencies=["analysis"],
        )
        t3 = Task(
            id="exploit",
            title="Exploit Generation",
            description="Construct reliable exploit script",
            estimated_duration=600,
            dependencies=["re"],
        )
        t4 = Task(
            id="flag",
            title="Flag Extraction",
            description="Execute exploit to extract CTF flag",
            estimated_duration=30,
            dependencies=["exploit"],
        )

        for t in [t1, t2, t3, t4]:
            graph.add_task(t)

        return self._build_plan_from_graph("Solve CTF challenge", graph)


class LearningStrategy(PlanningStrategy):
    def can_handle(self, context: PlannerContext) -> bool:
        if not context.intent:
            return False
        return (
            context.intent.intent_type in (IntentType.LEARNING, IntentType.LEARN)
            or "explain" in context.intent.raw_input.lower()
            or "learn" in context.intent.raw_input.lower()
        )

    def create_plan(self, context: PlannerContext) -> Plan:
        graph = TaskGraph()

        topic = (
            context.intent.raw_input.replace("Explain", "").replace("explain", "").strip()
            or "SQL Injection"
        )
        t1 = Task(
            id="concepts",
            title=f"{topic} Concepts",
            description=f"Learn core concepts of {topic}",
            estimated_duration=60,
        )
        t2 = Task(
            id="code_analysis",
            title="Vulnerable Code Analysis",
            description="Analyze vulnerable code examples",
            estimated_duration=120,
            dependencies=["concepts"],
        )
        t3 = Task(
            id="remediation",
            title="Remediation and Mitigation",
            description="Understand mitigation and secure patching",
            estimated_duration=90,
            dependencies=["code_analysis"],
        )

        for t in [t1, t2, t3]:
            graph.add_task(t)

        return self._build_plan_from_graph(f"Explain {topic}", graph)


class ReportStrategy(PlanningStrategy):
    def can_handle(self, context: PlannerContext) -> bool:
        if not context.intent:
            return False
        return (
            context.intent.intent_type == IntentType.REPORT
            or "report" in context.intent.raw_input.lower()
        )

    def create_plan(self, context: PlannerContext) -> Plan:
        graph = TaskGraph()

        t1 = Task(
            id="findings",
            title="Collate Findings",
            description="Collect verified target vulnerabilities",
            estimated_duration=10,
        )
        t2 = Task(
            id="markdown",
            title="Generate Markdown",
            description="Format findings into a Markdown report",
            estimated_duration=15,
            dependencies=["findings"],
        )
        t3 = Task(
            id="export",
            title="Export PDF/JSON",
            description="Compile and export final artifacts",
            estimated_duration=20,
            dependencies=["markdown"],
        )

        for t in [t1, t2, t3]:
            graph.add_task(t)

        return self._build_plan_from_graph("Compile final report", graph)

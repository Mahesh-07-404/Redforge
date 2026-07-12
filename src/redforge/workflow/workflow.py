from .contracts import WorkflowDefinition, WorkflowStage


class BuiltInWorkflows:
    @staticmethod
    def get_defaults() -> list[WorkflowDefinition]:
        return [
            WorkflowDefinition(
                id="passive_recon",
                name="Passive Recon",
                description="Performs passive reconnaissance on target",
                supported_intents=["PENTEST", "BUG_BOUNTY"],
                stages=[
                    WorkflowStage(
                        id="enum_subdomains",
                        name="Enumerate Subdomains",
                        agent="recon_agent",
                        planner_strategy="passive",
                        required_tools=["subfinder"],
                        policy_level="low",
                    )
                ],
            ),
            WorkflowDefinition(
                id="active_recon",
                name="Active Recon",
                description="Performs active reconnaissance on target",
                supported_intents=["PENTEST"],
                stages=[
                    WorkflowStage(
                        id="port_scan",
                        name="Port Scan",
                        agent="network_agent",
                        planner_strategy="active",
                        required_tools=["nmap"],
                        policy_level="medium",
                    )
                ],
            ),
            WorkflowDefinition(
                id="web_pentest",
                name="Web Pentest",
                description="Performs web pentesting check",
                supported_intents=["PENTEST"],
                stages=[
                    WorkflowStage(
                        id="web_scan",
                        name="Web Scan",
                        agent="web_agent",
                        planner_strategy="web",
                        required_tools=["httpx", "nuclei"],
                        policy_level="medium",
                    )
                ],
            ),
            WorkflowDefinition(
                id="bug_bounty",
                name="Bug Bounty",
                description="Runs bug bounty checks",
                supported_intents=["BUG_BOUNTY"],
                stages=[
                    WorkflowStage(
                        id="bounty_scan",
                        name="Bounty scan",
                        agent="bugbounty_agent",
                        planner_strategy="bugbounty",
                        required_tools=["subfinder", "httpx"],
                        policy_level="medium",
                    )
                ],
            ),
            WorkflowDefinition(
                id="ctf",
                name="CTF solver",
                description="Runs John/Hashcat solvers",
                supported_intents=["CTF"],
                stages=[
                    WorkflowStage(
                        id="ctf_solve",
                        name="Solve hash challenge",
                        agent="ctf_agent",
                        planner_strategy="ctf",
                        required_tools=["john"],
                        policy_level="low",
                    )
                ],
            ),
            WorkflowDefinition(
                id="learning",
                name="Learning guide",
                description="Explains concepts",
                supported_intents=["LEARNING"],
                stages=[
                    WorkflowStage(
                        id="concept_explain",
                        name="Explain concept",
                        agent="learning_agent",
                        planner_strategy="explain",
                        policy_level="low",
                    )
                ],
            ),
            WorkflowDefinition(
                id="report_generation",
                name="Report Generation",
                description="Compiles findings report",
                supported_intents=["REPORT"],
                stages=[
                    WorkflowStage(
                        id="gen_report",
                        name="Generate findings report",
                        agent="report_agent",
                        planner_strategy="report",
                        policy_level="low",
                    )
                ],
            ),
            WorkflowDefinition(
                id="research",
                name="Research CVEs",
                description="CVE research",
                supported_intents=["LEARNING"],
                stages=[
                    WorkflowStage(
                        id="cve_research",
                        name="Research CVE details",
                        agent="research_agent",
                        planner_strategy="research",
                        policy_level="low",
                    )
                ],
            ),
        ]

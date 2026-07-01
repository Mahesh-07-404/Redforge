from ..planner.task import Task


class TaskDecomposer:
    @staticmethod
    def decompose(goal_text: str) -> list[Task]:
        gt = goal_text.lower()
        tasks = []

        if "passive" in gt or "recon" in gt or "enumerate" in gt:
            tasks.append(
                Task(
                    id="subfinder",
                    title="Subdomain Recon",
                    description="Run subfinder",
                    tool_hint="subfinder",
                )
            )
            tasks.append(
                Task(
                    id="httpx",
                    title="HTTP Validation",
                    description="Run httpx",
                    tool_hint="httpx",
                    dependencies=["subfinder"],
                )
            )
            tasks.append(
                Task(
                    id="katana",
                    title="Web Crawl",
                    description="Run katana",
                    tool_hint="katana",
                    dependencies=["httpx"],
                )
            )
        elif "port" in gt or "scan" in gt:
            tasks.append(
                Task(id="nmap", title="Port scan", description="Run nmap", tool_hint="nmap")
            )
        elif "vuln" in gt or "scan" in gt or "nuclei" in gt:
            tasks.append(
                Task(
                    id="nuclei",
                    title="Vulnerability scan",
                    description="Run nuclei",
                    tool_hint="nuclei",
                )
            )
        else:
            tasks.append(
                Task(
                    id="subfinder",
                    title="Default Recon",
                    description="Run subfinder",
                    tool_hint="subfinder",
                )
            )

        return tasks

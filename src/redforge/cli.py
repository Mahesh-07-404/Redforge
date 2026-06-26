"""Enhanced CLI/TUI entry point for RedForge — React-Style Edition"""

from __future__ import annotations

import asyncio
import click
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

BANNER = """[bold red]
██████╗ ███████╗██████╗ ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
██╔══██╗██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
██████╔╝█████╗  ██║  ██║█████╗  ██║   ██║██████╔╝██║  ███╗█████╗  
██╔══██╗██╔══╝  ██║  ██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  
██║  ██║███████╗██████╔╝██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝[/bold red]
[dim]  Autonomous Penetration Testing AI  ·  Beast Edition  ·  v0.2.0[/dim]
"""

# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group(invoke_without_command=True)
@click.version_option(version="0.2.0")
@click.pass_context
def main(ctx):
    """RedForge — Autonomous CLI Pentesting Agent (LangGraph + Beast Mode)"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(tui)

# ---------------------------------------------------------------------------
# Recovered Commands
# ---------------------------------------------------------------------------

@main.command()
def status():
    """Show RedForge system status"""
    from redforge.core.config import get_settings
    from redforge.memory.workspace import WorkspaceManager
    from redforge.utils.platform import detect_platform

    settings = get_settings()
    console.print(Panel.fit("[bold]RedForge Status[/bold]"))

    platform_info = detect_platform()
    console.print(f"\n[cyan]Platform:[/cyan] {platform_info.os_name}")
    console.print(f"[cyan]Package Manager:[/cyan] {platform_info.package_manager.value}")
    console.print(f"\n[cyan]LLM:[/cyan] {settings.llm.provider} / {settings.llm.model}")
    console.print(f"[cyan]API Key:[/cyan] {'✓ set' if settings.llm.api_key else '✗ missing'}")
    console.print(f"\n[cyan]Autonomy:[/cyan] {settings.autonomy.default_level}")
    console.print(f"[cyan]Memory:[/cyan] {settings.memory.vector_db} @ {settings.memory.persist_dir}")

    wm = WorkspaceManager(settings.memory.persist_dir)
    workspaces = wm.list_workspaces()
    console.print(f"\n[cyan]Workspaces:[/cyan] {len(workspaces)}")

    # Skills check
    from redforge.core.skill_loader import SkillLoader
    sl = SkillLoader()
    sl.load_skills()
    s = sl.stats()
    console.print(f"[cyan]Skills:[/cyan] {s['total']} ({'' if s['dir_exists'] else '⚠ dir missing: '}{s['skills_dir']})")


@main.command()
def doctor():
    """Check system health and dependencies"""
    from redforge.core.config import get_settings
    from redforge.core.agent import RedForgeAgent
    from redforge.utils.platform import check_tool_available, detect_platform, get_tool_version

    console.print(Panel.fit("[bold]🩺 System Health Check[/bold]"))

    settings = get_settings()
    platform_info = detect_platform()
    console.print(f"\n[cyan]OS:[/cyan] {platform_info.os_name} {platform_info.os_version}")
    console.print(f"[cyan]Package Manager:[/cyan] {platform_info.package_manager.value}")

    console.print("\n[cyan]LLM Provider:[/cyan]")
    agent = RedForgeAgent(
        config=settings,
        llm_provider=settings.llm.provider,
        model=settings.llm.model,
        api_key=settings.llm.api_key,
        base_url=settings.llm.base_url,
    )
    llm_ok = agent.llm.is_available()
    console.print(f"  Provider: {agent.llm.model}  {'[green]✓[/green]' if llm_ok else '[red]✗[/red]'}")

    console.print("\n[cyan]Skills:[/cyan]")
    sl_stats = agent.skill_loader.stats()
    sl_stats_after_load = (agent.skill_loader.load_skills() or True) and agent.skill_loader.stats()
    console.print(f"  Dir: {sl_stats['skills_dir']}")
    console.print(f"  Exists: {'[green]✓[/green]' if sl_stats['dir_exists'] else '[red]✗[/red]'}")
    console.print(f"  Total loaded: {sl_stats_after_load['total']}")

    console.print("\n[cyan]Tools:[/cyan]")
    tools_to_check = ["python3", "git", "curl", "nmap", "ffuf", "sqlmap", "whatweb", "dig", "whois"]
    for tool in tools_to_check:
        available, path = check_tool_available(tool)
        version = get_tool_version(tool) if available else None
        status_icon = "[green]✓[/green]" if available else "[red]✗[/red]"
        ver_str = f" ({version[:40]})" if version else ""
        console.print(f"  {status_icon} {tool}: {path or 'not found'}{ver_str}")


@main.command()
def tui():
    """Launch the Claude-style terminal UI"""
    try:
        from redforge.tui import launch_tui
    except Exception as exc:
        console.print(f"[red]Unable to load TUI:[/red] {exc}")
        return

    launch_tui()


@main.command()
@click.option("--host", default="127.0.0.1", show_default=True, help="Host to bind the server to")
@click.option("--port", default=8000, show_default=True, type=int, help="Port to run the server on")
def web(host, port):
    """Launch the web-based monitoring dashboard"""
    console.print(Panel.fit("[bold]🌐 RedForge Web Dashboard[/bold]"))
    console.print(f"Starting server on [cyan]http://{host}:{port}[/cyan]...")
    
    try:
        import uvicorn
        from redforge.web.app import app
        uvicorn.run(app, host=host, port=port)
    except Exception as exc:
        console.print(f"[red]Unable to load or run Web Dashboard:[/red] {exc}")


@main.command()
@click.option("--persist-dir", default="./workspaces")
def workspaces(persist_dir):
    """List all workspaces"""
    from redforge.memory.workspace import WorkspaceManager

    wm = WorkspaceManager(persist_dir)
    all_ws = wm.list_workspaces()
    if not all_ws:
        console.print("[yellow]No workspaces found.[/yellow]")
        return
    t = Table(title="Workspaces")
    t.add_column("ID", style="cyan")
    t.add_column("Name")
    t.add_column("Created", style="green")
    t.add_column("Last Accessed", style="yellow")
    for ws in all_ws:
        t.add_row(ws.id[:8], ws.name,
                  ws.created_at.strftime("%Y-%m-%d"),
                  ws.last_accessed.strftime("%Y-%m-%d %H:%M"))
    console.print(t)


@main.command(name="create-workspace")
@click.argument("name")
@click.option("--persist-dir", default="./workspaces")
def create_workspace(name, persist_dir):
    """Create a new workspace"""
    from redforge.memory.workspace import WorkspaceManager

    wm = WorkspaceManager(persist_dir)
    ws = wm.create_workspace(name)
    console.print(f"[green]Created:[/green] {ws.name} ({ws.id[:8]})")


@main.command()
@click.option("--workspace", "-w", default="default")
def memory(workspace):
    """Show memory stats for a workspace"""
    from redforge.core.config import get_settings
    from redforge.memory.memory_manager import WorkspaceMemoryManager
    from redforge.memory.workspace import WorkspaceManager

    settings = get_settings()
    wm = WorkspaceManager(settings.memory.persist_dir)
    ws = wm.get_workspace_by_name(workspace)
    if not ws:
        console.print(f"[yellow]Workspace '{workspace}' not found.[/yellow]")
        return
    mm = WorkspaceMemoryManager(ws.id, settings.memory.persist_dir, settings.memory.vector_db)
    stats = mm.get_stats()
    console.print(Panel.fit(f"[bold]Memory: {workspace}[/bold]"))
    console.print(f"\nSessions: {stats.get('total_sessions', 0)}")
    console.print(f"Findings: {stats.get('total_findings', 0)}")
    console.print(f"Notes: {stats.get('total_notes', 0)}")
    console.print(f"Vector Store: {'[green]✓[/green]' if stats.get('vector_store_available', False) else '[red]✗[/red]'}")


@main.command()
@click.argument("query")
@click.option("--workspace", "-w", default="default")
@click.option("--limit", "-l", default=5)
def search(query, workspace, limit):
    """Search workspace memory"""
    from redforge.core.config import get_settings
    from redforge.memory.memory_manager import WorkspaceMemoryManager
    from redforge.memory.workspace import WorkspaceManager

    settings = get_settings()
    wm = WorkspaceManager(settings.memory.persist_dir)
    ws = wm.get_workspace_by_name(workspace)
    if not ws:
        console.print(f"[yellow]Workspace '{workspace}' not found.[/yellow]")
        return
    mm = WorkspaceMemoryManager(ws.id, settings.memory.persist_dir, settings.memory.vector_db)
    results = mm.search(query, limit=limit)
    if not results:
        console.print("[yellow]No results.[/yellow]")
        return
    console.print(f"[cyan]Found {len(results)} results:[/cyan]\n")
    for i, r in enumerate(results, 1):
        console.print(f"[bold]{i}.[/bold] [score: {r.score:.2f}]")
        console.print(f"   {r.content[:120]}…\n")


@main.command()
def skills():
    """Show skill index stats"""
    from redforge.core.skill_loader import SkillLoader
    sl = SkillLoader()
    sl.load_skills()
    s = sl.stats()
    console.print(Panel.fit("[bold]Skill Index[/bold]"))
    console.print(f"\nDirectory: {s['skills_dir']}")
    console.print(f"Exists: {'[green]✓[/green]' if s['dir_exists'] else '[red]✗[/red]'}")
    console.print(f"Total skills: {s['total']}")
    if s["by_category"]:
        console.print("\n[cyan]By Category:[/cyan]")
        for cat, count in sorted(s["by_category"].items()):
            console.print(f"  {cat}: {count}")


@main.command()
@click.option("--workspace", "-w", default="default", help="Workspace to report on")
@click.option("--output", "-o", default=None, help="Output file path (default: ./report_<workspace>.md)")
@click.option("--format", "fmt", type=click.Choice(["markdown", "json", "both"]), default="both")
def report(workspace, output, fmt):
    """Generate a security findings report from a workspace"""
    from redforge.core.config import get_settings
    from redforge.memory.memory_manager import WorkspaceMemoryManager
    from redforge.memory.workspace import WorkspaceManager

    settings = get_settings()
    wm = WorkspaceManager(settings.memory.persist_dir)
    ws = wm.get_workspace_by_name(workspace)

    if not ws:
        console.print(f"[red]Workspace '{workspace}' not found.[/red]")
        return

    mm = WorkspaceMemoryManager(ws.id, settings.memory.persist_dir, settings.memory.vector_db)
    findings = mm.list_findings()

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    out_stem = output or f"./report_{workspace}"

    # Generate Markdown stub
    if fmt in ("markdown", "both"):
        md_path = Path(out_stem + ".md") if not out_stem.endswith(".md") else Path(out_stem)
        console.print(f"[green]✓ Markdown report generated at:[/green] {md_path}")
        with open(md_path, "w") as f:
            f.write(f"# Report for {workspace}\n\nGenerated on {ts}\nFindings count: {len(findings)}")

    if fmt in ("json", "both"):
        json_path = Path(out_stem + ".json") if not out_stem.endswith(".json") else Path(out_stem)
        console.print(f"[green]✓ JSON report generated at:[/green] {json_path}")
        with open(json_path, "w") as f:
            f.write(f'{{"workspace": "{workspace}", "findings_count": {len(findings)}}}')


@main.command()
@click.option("--mode", "-m", type=click.Choice(["bugbounty", "ctf", "learning", "coding", "android"]), default="bugbounty", show_default=True, help="Operating mode")
@click.option("--workspace", "-w", default="default", help="Workspace name")
@click.option("--autonomy", "-a", type=click.Choice(["manual", "partial", "full"]), default="full", show_default=True, help="Autonomy level")
@click.option("--provider", "-p", default=None, help="LLM provider override")
@click.option("--model", default=None, help="Model override")
@click.option("--target", "-t", required=True, help="Target domain/IP")
def run(mode, workspace, autonomy, provider, model, target):
    """Run RedForge in non-interactive headless mode for automation"""
    from redforge.core.autonomy_controller import AutonomyLevel
    from redforge.core.config import get_settings
    from redforge.core.factory import create_redforge_agent
    from redforge.memory.workspace import WorkspaceManager
    from redforge.core.state import AgentMode

    console.print(BANNER)
    console.print(f"[bold red]RedForge Headless Runner[/bold red] starting on target: [cyan]{target}[/cyan]")

    settings = get_settings()
    wm = WorkspaceManager(settings.memory.persist_dir)
    ws = wm.get_or_create_workspace(workspace)

    agent = create_redforge_agent(
        config=settings,
        llm_provider=provider or settings.llm.provider,
        model=model or settings.llm.model,
        api_key=settings.llm.api_key,
        base_url=settings.llm.base_url,
    )

    autonomy_level = AutonomyLevel(autonomy)
    
    mode_map = {
        "bugbounty": AgentMode.GOAL_BASED,
        "ctf": AgentMode.GOAL_BASED,
        "android": AgentMode.GOAL_BASED,
        "learning": AgentMode.KNOWLEDGE_BASED,
        "coding": AgentMode.KNOWLEDGE_BASED,
    }

    # Set up event callback to log actions to stdout
    def log_event(payload):
        evt = payload.get("event")
        if evt == "tool_start":
            console.print(f"[yellow]▶ Tool Execution:[/yellow] {payload.get('tool_name')} ({payload.get('command')})")
        elif evt == "tool_end":
            status = payload.get("status")
            status_color = "green" if status == "done" else "red"
            console.print(f"  [{status_color}✓[/{status_color}] Status: {status}")
        elif evt == "finding":
            console.print(f"[red]⚠ FINDING:[/red] {payload.get('description')} ({payload.get('severity')})")

    agent.on("*", log_event)

    # Execute the agent loop
    user_input = f"Perform security analysis on {target}."
    async def execute():
        state = await agent.run(
            user_input=user_input,
            workspace_id=ws.id,
            workspace_name=ws.name,
            autonomy_level=autonomy_level,
            mode=mode_map.get(mode, AgentMode.GOAL_BASED),
            active_mode=mode,
        )
        console.print(f"\n[green]Execution finished.[/green] Total tokens used: {state.total_tokens}")
        if state.findings:
            console.print(f"[bold]Total findings discovered: {len(state.findings)}[/bold]")
            for idx, f in enumerate(state.findings, 1):
                console.print(f"  {idx}. [{f.get('severity', 'medium').upper()}] {f.get('title')}: {f.get('description')}")
        else:
            console.print("No findings discovered.")

    asyncio.run(execute())

"""Enhanced CLI entry point for RedForge — React-Style Edition"""

from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

import click
from rich import print as rprint
from rich.columns import Columns
from rich.console import Console
from rich.console import Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.markup import escape

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style as PtStyle
from prompt_toolkit.shortcuts import CompleteStyle

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
# React-style Active Block Engine
# ---------------------------------------------------------------------------

SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

class ActiveBlock:
    """Represents the currently rendering dynamic element in the Live loop."""
    def __init__(self):
        self.frame_idx = 0
        self.status = "thinking" # thinking | streaming | done | error
        self.output_buffer = ""
        self.stream_queue = []
        self.start_time = time.monotonic()
        self.mode = "bugbounty"
        self.workspace = "default"
        
    def tick(self):
        """Update animations or stream drain."""
        self.frame_idx += 1
        if self.status == "streaming" and self.stream_queue:
            # Drain up to 8 chars per tick
            chunk = "".join(self.stream_queue[:8])
            self.stream_queue = self.stream_queue[8:]
            self.output_buffer += chunk
            if not self.stream_queue:
                self.status = "done"

    def __rich__(self):
        """Rich protocol render mapping."""
        spinner = f"[bold #ffcc00]{SPINNER_FRAMES[self.frame_idx % len(SPINNER_FRAMES)]}[/bold #ffcc00]"
        elapsed = time.monotonic() - self.start_time
        mode_color = {"bugbounty": "red", "ctf": "cyan", "learning": "green", "coding": "blue", "android": "yellow"}.get(self.mode, "magenta")
        meta = f"[{mode_color}]{self.mode.upper()}[/{mode_color}]  [dim]ws={escape(self.workspace)}  {elapsed:.1f}s[/dim]"
        if self.status == "thinking":
            return Panel(
                Group(
                    Rule(style="dim"),
                    f"{spinner}  [bold]RedForge is thinking[/bold]",
                    meta,
                    "[dim]Planning next step, loading context, and preparing actions.[/dim]",
                ),
                border_style="dim",
                title="Live Session",
            )
        elif self.status == "streaming":
            return Panel(
                Group(
                    f"{spinner}  [bold #ff4f00]Streaming response[/bold #ff4f00]",
                    meta,
                    Rule(style="dim"),
                    Markdown(self.output_buffer),
                ),
                border_style="#ff4f00",
                title="Assistant",
            )
        elif self.status == "error":
            return Panel(self.output_buffer, border_style="red", title="Error")
        else:
            return Panel(Markdown(self.output_buffer), border_style="dim", title="Assistant")

# ---------------------------------------------------------------------------
# chat
# ---------------------------------------------------------------------------

@main.command()
@click.option("--mode", "-m",
              type=click.Choice(["bugbounty", "ctf", "learning", "coding", "android"]),
              default="bugbounty", show_default=True, help="Operating mode")
@click.option("--workspace", "-w", default=None, help="Workspace name")
@click.option("--autonomy", "-a",
              type=click.Choice(["manual", "partial", "full"]),
              default="manual", show_default=True, help="Autonomy level")
@click.option("--provider", "-p",
              type=click.Choice(["ollama", "openai", "anthropic", "groq", "gemini"]),
              default=None, help="LLM provider override")
@click.option("--model", default=None, help="Model override")
@click.option("--target", "-t", default=None, help="Initial target")
def chat(mode, workspace, autonomy, provider, model, target):
    """Start an interactive React-style pentesting chat session"""
    from redforge.core.autonomy_controller import AutonomyController, AutonomyLevel
    from redforge.core.config import get_settings
    from redforge.core.langgraph_agent import RedForgeAgent
    from redforge.memory.workspace import WorkspaceManager

    console.print(BANNER)

    settings = get_settings()
    workspace = workspace or settings.workspace.default_workspace

    wm = WorkspaceManager(settings.memory.persist_dir)
    ws = wm.get_or_create_workspace(workspace)

    agent = RedForgeAgent(
        config=settings,
        llm_provider=provider or settings.llm.provider,
        model=model or settings.llm.model,
        api_key=settings.llm.api_key,
        base_url=settings.llm.base_url,
    )

    autonomy_level = AutonomyLevel(autonomy)
    autonomy_ctrl = AutonomyController(
        default_level=autonomy_level,
        max_level=AutonomyLevel[autonomy.upper()],
    )

    info = Table.grid(padding=(0, 2))
    info.add_row("[cyan]Workspace[/cyan]", ws.name)
    info.add_row("[cyan]Mode[/cyan]", mode.upper())
    info.add_row("[cyan]Autonomy[/cyan]", autonomy.upper())
    info.add_row("[cyan]LLM[/cyan]", f"{provider or settings.llm.provider} / {model or settings.llm.model}")
    if target:
        info.add_row("[cyan]Target[/cyan]", target)
    console.print(Panel(info, title="[bold]Session Config[/bold]", border_style="dim"))

    if autonomy == "full":
        console.print(Panel(
            "[bold red]⚠  FULL AUTONOMY — all actions execute automatically.\n"
            "Ensure you have written authorization for the target.[/bold red]",
            border_style="red",
        ))

    asyncio.run(_chat_loop(agent, autonomy_ctrl, mode, ws, target))


async def _chat_loop(agent, autonomy_ctrl, mode, workspace, initial_target=None):
    """React-style interaction loop with prompt_toolkit and rich.live."""
    from redforge.core.autonomy_controller import AutonomyLevel
    from redforge.core.loop_detector import LoopDetector
    from redforge.core.state import AgentMode

    loop_detector = LoopDetector(
        max_iterations=agent.max_iterations,
        loop_threshold=agent.loop_threshold,
    )

    prior_state = None
    mode_map = {
        "bugbounty": AgentMode.GOAL_BASED,
        "ctf": AgentMode.GOAL_BASED,
        "learning": AgentMode.KNOWLEDGE_BASED,
        "coding": AgentMode.KNOWLEDGE_BASED,
        "android": AgentMode.GOAL_BASED,
    }
    agent_mode = mode_map.get(mode, AgentMode.GOAL_BASED)

    console.print("\n[dim]Commands: /help, /status, /findings, /clear, /exit[/dim]")

    session = PromptSession(history=InMemoryHistory())
    pt_style = PtStyle.from_dict({'prompt': 'bold #00d4ff'})

    if initial_target:
        console.print(f"[dim]Auto-injecting target: {initial_target}[/dim]")
        first_input = f"My target is {initial_target}. Begin reconnaissance."
    else:
        first_input = None

    while True:
        try:
            if first_input:
                user_input = first_input
                first_input = None
            else:
                user_input = await session.prompt_async("\n▶ ", style=pt_style)

            if not user_input.strip():
                continue

            cmd = user_input.strip().lower()
            if cmd in ("/exit", "/quit", "/q", "exit", "quit", "q"):
                console.print("[yellow]Goodbye![/yellow]")
                break
            if cmd == "/help" or cmd == "help":
                _print_help()
                continue
            if cmd == "/status" or cmd == "status":
                _print_status(agent, autonomy_ctrl, loop_detector, prior_state)
                continue
            if cmd == "/findings" or cmd == "findings":
                _print_findings(prior_state)
                continue
            if cmd == "approved" or cmd == "/approved":
                run_autonomy = AutonomyLevel.PARTIAL
                run_input = "[APPROVED] Execute the planned action."
            else:
                run_autonomy = autonomy_ctrl.current_level
                run_input = user_input

            # Print user message to terminal history
            console.print(f"\n[bold #ff4f00]▶ You[/bold #ff4f00]\n  {escape(run_input)}\n")

            # Inline render context
            active_block = ActiveBlock()
            active_block.mode = mode
            active_block.workspace = workspace.name
            
            with Live(active_block, console=console, refresh_per_second=15, transient=True) as live:
                # 1. Run agent task in background
                task = asyncio.create_task(agent.run(
                    user_input=run_input,
                    workspace_id=workspace.id,
                    workspace_name=workspace.name,
                    autonomy_level=run_autonomy,
                    mode=agent_mode,
                    prior_state=prior_state,
                ))

                while not task.done():
                    active_block.tick()
                    live.refresh()
                    await asyncio.sleep(0.06)

                try:
                    state = task.result()
                    if state.error:
                        active_block.status = "error"
                        active_block.output_buffer = f"Agent error: {state.error}"
                        live.refresh()
                        await asyncio.sleep(0.8)
                        console.print(Panel(state.error, title="[bold red]Agent Error[/bold red]", border_style="red"))
                        continue
                except Exception as exc:
                    active_block.status = "error"
                    active_block.output_buffer = f"Agent error: {exc}"
                    live.refresh()
                    await asyncio.sleep(0.5)
                    console.print(active_block) # print final error
                    continue
                
                # 2. Process returning messages and findings
                prior_len = len(prior_state.messages) if prior_state else 0
                new_messages = state.messages[prior_len:]
                
                # We will extract assistant messages and animate them 
                combined_output = ""
                for msg in new_messages:
                    r, c = msg.get("role", ""), msg.get("content", "")
                    if r == "assistant":
                        combined_output += c + "\n\n"
                        
                if combined_output:
                    active_block.status = "streaming"
                    active_block.stream_queue = list(combined_output)
                    while active_block.status != "done":
                        active_block.tick()
                        live.refresh()
                        await asyncio.sleep(0.02)
                
                prior_state = state
                loop_detector.record_state(state.model_dump())

            # 3. Print Final output to terminal history
            # Assistant response
            _render_state_output(state, prior_len)

            # Warning for tools
            if state.pending_confirmation:
                console.print(Panel(
                    "[yellow]⚠  Agent wants to run a tool.[/yellow]\n"
                    "Type [bold]/approved[/bold] to execute, or give new instructions.",
                    border_style="yellow",
                    title="Manual Approval Required",
                ))

            # Loop warning
            loop_result = loop_detector.detect_loop()
            if loop_result.is_looping:
                console.print(f"[yellow]⚠  {loop_result.message}[/yellow]")
            if loop_result.should_stop:
                console.print("[red]Stopping — loop limit hit.[/red]")
                break

        except KeyboardInterrupt:
            console.print("\n[yellow]Ctrl-C — type '/exit' to quit.[/yellow]")
        except Exception as exc:
            console.print(f"[red]Error:[/red] {exc}")


def _render_state_output(state, prior_len):
    """Renders finalized messages to the terminal scrollback."""
    new_messages = state.messages[prior_len:]
    for msg in new_messages:
        role = msg.get("role", "")
        content = msg.get("content", "")

        if role == "assistant":
            console.print(Rule("⛏ RedForge", style="cyan dim"))
            console.print(Markdown(content))
        elif role == "tool":
            console.print(Rule("Tool Output", style="yellow dim"))
            console.print(Syntax(content, "bash", theme="monokai", word_wrap=True))
            
    # Print findings
    prior_findings = len(state.findings) - len(new_messages) # approximate
    for f in state.findings:
        # Simple deduplication print - could be improved
        sev = f.get("severity", "info").upper()
        sc = {"CRITICAL": "red", "HIGH": "bright_red", "MEDIUM": "yellow"}.get(sev, "dim")
        console.print(Panel(
            f"[{sc}][{sev}][/{sc}] {f.get('title', '')}\n[dim]{f.get('type', '')}[/dim]",
            border_style=sc
        ))


def _print_help():
    t = Table(title="RedForge Commands", show_header=True, header_style="bold cyan")
    t.add_column("Command", style="cyan", no_wrap=True)
    t.add_column("Description")
    rows = [
        ("/exit", "Exit the session"),
        ("/help", "Show this help"),
        ("/status", "Agent and autonomy status"),
        ("/findings", "List discovered findings"),
        ("/approved", "Approve a pending tool action"),
    ]
    for cmd, desc in rows:
        t.add_row(cmd, desc)
    console.print(t)


def _print_status(agent, autonomy_ctrl, loop_detector, state):
    agent_status = agent.get_status()
    auto_status = autonomy_ctrl.get_status()
    loop_status = loop_detector.get_status()

    t = Table(title="Agent Status", show_header=False)
    t.add_column("Property", style="cyan", no_wrap=True)
    t.add_column("Value")
    t.add_row("LLM", agent_status["llm_provider"])
    t.add_row("Skills loaded", str(agent_status["skills_total"]))
    t.add_row("Autonomy", auto_status["current_level"])
    t.add_row("Consent", "✓" if auto_status["consent_given"] else "✗")
    t.add_row("Iteration", f"{loop_status['iteration']}/{loop_status['max_iterations']}")
    t.add_row("Tool calls", str(agent_status.get("tool_history", 0)))
    if state:
        t.add_row("Findings", str(len(state.findings)))
    console.print(t)


def _print_findings(state):
    if not state or not state.findings:
        console.print("[dim]No findings yet.[/dim]")
        return
    t = Table(title=f"Findings ({len(state.findings)})", show_header=True, header_style="bold red")
    t.add_column("#", style="dim", width=3)
    t.add_column("Severity", style="bold")
    t.add_column("Type")
    t.add_column("Title")
    sev_colors = {"critical": "red", "high": "bright_red", "medium": "yellow",
                  "low": "blue", "info": "dim"}
    for i, f in enumerate(state.findings, 1):
        sev = f.get("severity", "info")
        color = sev_colors.get(sev, "white")
        t.add_row(str(i), f"[{color}]{sev.upper()}[/{color}]",
                  f.get("type", "?"), f.get("title", "")[:60])
    console.print(t)


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
    from redforge.core.langgraph_agent import RedForgeAgent
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


@main.command()
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
    sessions = mm.list_sessions(limit=50)

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

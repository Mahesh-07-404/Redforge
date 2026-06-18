"""Enhanced CLI entry point for RedForge — React-Style Edition"""

from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
import uuid
import json
from redforge.core.database import SessionDatabase
from redforge.core.state import AgentState


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
    from redforge.core.factory import create_redforge_agent
    from redforge.memory.workspace import WorkspaceManager

    console.print(BANNER)

    settings = get_settings()
    workspace = workspace or settings.workspace.default_workspace

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


def _reconstruct_prior_state(db, session_id, ws_id, ws_name, current_target, current_mode, current_autonomy) -> AgentState:
    from redforge.core.state import AgentState, AgentMode, AutonomyLevel
    from datetime import datetime
    messages_db = db.get_messages(session_id)
    findings_db = db.get_findings(session_id)
    tasks_db = db.get_tasks(session_id)
    
    agent_messages = []
    for m in messages_db:
        ts = m["timestamp"]
        if isinstance(ts, (int, float)):
            ts_str = datetime.fromtimestamp(ts).isoformat()
        else:
            ts_str = str(ts)
            
        agent_messages.append({
            "role": m["role"],
            "content": m["content"],
            "timestamp": ts_str
        })
    
    mode_map = {
        "bugbounty": AgentMode.GOAL_BASED,
        "ctf": AgentMode.GOAL_BASED,
        "learning": AgentMode.KNOWLEDGE_BASED,
        "coding": AgentMode.KNOWLEDGE_BASED,
        "android": AgentMode.GOAL_BASED,
    }
    
    return AgentState(
        messages=agent_messages,
        target=current_target,
        workspace_id=ws_id,
        workspace_name=ws_name,
        autonomy_level=AutonomyLevel(current_autonomy),
        mode=mode_map.get(current_mode, AgentMode.GOAL_BASED),
        findings=findings_db,
        tasks=tasks_db,
        iteration=0,
        loop_count=0
    )


async def _chat_loop(agent, autonomy_ctrl, mode, workspace, initial_target=None):
    """React-style interaction loop with prompt_toolkit and rich.live."""
    import re
    import os
    import json
    from pathlib import Path
    from datetime import datetime
    from prompt_toolkit.completion import Completer, Completion
    from redforge.core.autonomy_controller import AutonomyLevel
    from redforge.core.loop_detector import LoopDetector
    from redforge.core.state import AgentMode
    from redforge.tui.palette import CommandRegistry
    from redforge.core.config import get_settings

    MODES = ["bugbounty", "ctf", "learning", "coding", "android"]

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

    db = SessionDatabase()
    latest = db.list_sessions()
    session_id = str(uuid.uuid4())
    session_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    settings = get_settings()
    current_target = initial_target or ""
    current_mode = mode
    current_autonomy = autonomy_ctrl.current_level.value
    current_provider = agent.llm.provider if hasattr(agent, "llm") and agent.llm else settings.llm.provider
    current_model = agent.llm.model if hasattr(agent, "llm") and agent.llm else settings.llm.model

    project_root = Path.cwd()
    project_files = []
    attached_files = []

    def refresh_project_files():
        nonlocal project_files
        files = []
        ignored = {".git", "__pycache__", ".venv", "venv", "node_modules", "dist", "build"}
        if not project_root.exists():
            return
        for current_root, dirs, names in os.walk(project_root):
            dirs[:] = [name for name in dirs if name not in ignored and not name.startswith(".")]
            for name in sorted(names):
                if name.startswith("."):
                    continue
                files.append(Path(current_root) / name)
        project_files = files

    refresh_project_files()

    def resolve_project_path(raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = project_root / path
        return path.resolve()

    def format_relpath(path: Path) -> str:
        try:
            return str(path.relative_to(project_root))
        except Exception:
            return str(path)

    def read_file_context(path: Path, limit: int = 3000) -> str:
        try:
            data = path.read_bytes()
        except Exception as exc:
            return f"{format_relpath(path)}: failed to read ({exc})"
        metadata = f"Path: {format_relpath(path)} | Ext: {path.suffix or 'none'} | Dir: {format_relpath(path.parent)}"
        if b"\x00" in data[:512]:
            preview = data[:32].hex()
            return f"FILE METADATA: {metadata} | Type: binary | Size: {len(data)} bytes\nCONTENT PREVIEW: {preview}"
        text = data.decode("utf-8", errors="replace")
        trimmed = text[:limit]
        if len(text) > limit:
            trimmed += "\n[TRUNCATED]"
        return f"FILE METADATA: {metadata}\nCONTENT:\n{trimmed}"

    def build_message_with_file_context(message: str) -> str:
        paths = []
        seen = set()
        for match in re.finditer(r"@([^\s]+)", message):
            raw = match.group(1).rstrip(".,:;!?)]}")
            if not raw:
                continue
            path = resolve_project_path(raw)
            if path.exists() and path not in seen:
                seen.add(path)
                paths.append(path)
        combined = []
        seen_comb = set()
        for path in [*paths, *attached_files]:
            if path.exists() and path not in seen_comb:
                seen_comb.add(path)
                combined.append(path)
        if not combined:
            return message
        file_context = "\n\n".join(read_file_context(path) for path in combined[:6])
        return (
            f"{message}\n\n"
            f"Project file context from {project_root}:\n"
            f"{file_context}\n"
        )

    # Event handlers for database logging
    def on_agent_assistant_end(payload):
        content = payload.get("content", "")
        if content:
            db.add_message(
                session_id=session_id,
                role="assistant",
                content=content
            )

    def on_agent_tool_end(payload):
        result = payload.get("result", {}) or {}
        output = result.get("output") or payload.get("error") or "(no output)"
        db.add_message(
            session_id=session_id,
            role="tool",
            content=output,
            tool_name=payload.get("tool", "tool"),
            command=payload.get("command", ""),
            status="done" if payload.get("success") else "failed",
            duration_s=float(result.get("duration_s", 0.0) or 0.0)
        )

    def on_agent_finding(payload):
        finding = payload.get("finding", {})
        if finding:
            db.add_finding(
                session_id=session_id,
                id=finding.get("id") or str(uuid.uuid4()),
                type=finding.get("type") or "finding",
                title=finding.get("title") or "Vulnerability Finding",
                description=finding.get("description") or "",
                severity=finding.get("severity") or "medium",
                target=current_target,
                evidence=finding.get("evidence")
            )
            db.add_message(
                session_id=session_id,
                role="finding",
                content=finding.get("description") or "",
                tool_name=finding.get("type") or "finding",
                severity=finding.get("severity") or "medium"
            )

    def rebuild_agent(prov: str, mod: str):
        nonlocal agent
        from redforge.core.agent import RedForgeAgent
        agent = RedForgeAgent(
            config=settings,
            llm_provider=prov,
            model=mod,
            api_key=settings.llm.api_key,
            base_url=settings.llm.base_url,
        )
        agent.on("assistant_end", on_agent_assistant_end)
        agent.on("tool_end", on_agent_tool_end)
        agent.on("finding", on_agent_finding)

    # Bind initial handlers
    agent.on("assistant_end", on_agent_assistant_end)
    agent.on("tool_end", on_agent_tool_end)
    agent.on("finding", on_agent_finding)

    resume = False
    if latest:
        last_sess = latest[0]
        last_id = last_sess["id"]
        last_name = last_sess["name"]
        last_target = last_sess.get("target") or "not set"
        last_findings = db.get_findings(last_id)
        open_tasks = [t for t in db.get_tasks(last_id) if t["status"] in ("pending", "in_progress")]
        
        console.print(Panel(
            f"[cyan]Last Session:[/cyan] {last_name} ({last_id[:8]})\n"
            f"[cyan]Last Target:[/cyan] {last_target}\n"
            f"[cyan]Last Findings:[/cyan] {len(last_findings)}\n"
            f"[cyan]Open Tasks:[/cyan] {len(open_tasks)}",
            title="[bold]Continuity Check - Previous Session Found[/bold]",
            border_style="green"
        ))
        for t in open_tasks:
            console.print(f"  - [ ] {t['description']}")
            
        ans = input("Resume last session? (Y/n): ").strip().lower()
        if ans in ("", "y", "yes"):
            resume = True
            session_id = last_id
            session_name = last_name
            current_target = last_sess.get("target") or ""
            current_mode = last_sess.get("mode") or "bugbounty"
            current_autonomy = last_sess.get("autonomy") or "manual"
            db_model = last_sess.get("model") or ""
            if db_model and "/" in db_model:
                current_provider, current_model = db_model.split("/", 1)
                rebuild_agent(current_provider, current_model)
            prior_state = _reconstruct_prior_state(db, session_id, workspace.id, workspace.name, current_target, current_mode, current_autonomy)
            console.print(f"[green]Resumed session '{session_name}' ({session_id[:8]})[/green]")
        else:
            db.create_session(session_id, session_name, current_mode, current_autonomy, f"{current_provider}/{current_model}", current_target)
            console.print(f"[green]Started new session '{session_name}' ({session_id[:8]})[/green]")
    else:
        db.create_session(session_id, session_name, current_mode, current_autonomy, f"{current_provider}/{current_model}", current_target)
        console.print(f"[green]Started new session '{session_name}' ({session_id[:8]})[/green]")

    class RedForgeCompleter(Completer):
        def get_completions(self, document, complete_event):
            text = document.text_before_cursor
            
            # File Mentions
            file_match = re.search(r'@([^\s]*)$', text)
            if file_match:
                prefix = file_match.group(1)
                start_position = -len(prefix) - 1
                rel_files = [format_relpath(p) for p in project_files]
                att_files = [format_relpath(p) for p in attached_files]
                all_files = sorted(list(set(att_files + rel_files)))
                for f in all_files:
                    if f.lower().startswith(prefix.lower()):
                        yield Completion(f"@{f}", start_position=start_position)
                return
                
            # Slash commands
            if text.startswith("/"):
                parts = text.split()
                if len(parts) <= 1 and not text.endswith(" "):
                    prefix = text
                    for cmd_entry in CommandRegistry.get_commands():
                        cmd = cmd_entry["cmd"]
                        desc = cmd_entry["desc"]
                        if cmd.startswith(prefix):
                            yield Completion(cmd, start_position=-len(prefix), display_meta=desc)
                elif len(parts) >= 1:
                    base_cmd = parts[0]
                    nested = CommandRegistry.get_nested_commands(base_cmd)
                    if nested:
                        if len(parts) == 2 and not text.endswith(" "):
                            prefix = parts[1]
                            for n in nested:
                                if n["cmd"].startswith(prefix):
                                    yield Completion(n["cmd"], start_position=-len(prefix), display_meta=n["desc"])
                        elif len(parts) == 1 and text.endswith(" "):
                            for n in nested:
                                yield Completion(n["cmd"], start_position=0, display_meta=n["desc"])

    console.print("\n[dim]Commands: /help, /status, /findings, /clear, /exit[/dim]")

    session = PromptSession(
        history=InMemoryHistory(),
        completer=RedForgeCompleter(),
        complete_style=CompleteStyle.READLINE_LIKE
    )
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

            clean_input = user_input.strip()
            if not clean_input:
                continue

            if clean_input.startswith("/"):
                parts = clean_input[1:].split(maxsplit=1)
                cmd = parts[0].lower() if parts else ""
                arg = parts[1].strip() if len(parts) > 1 else ""
                
                if not CommandRegistry.exists(clean_input):
                    base_cmd = f"/{cmd}"
                    if not CommandRegistry.exists(base_cmd):
                        console.print(f"[red]Command Failed: {clean_input}. Reason: Command does not exist in registry.[/red]")
                        continue

                if cmd == "help":
                    _print_help()
                    continue
                elif cmd == "clear":
                    console.clear()
                    continue
                elif cmd in ("exit", "quit", "q"):
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                elif cmd == "mode":
                    if not arg:
                        console.print(f"Current mode: {current_mode}")
                        ans = input(f"Select mode ({'/'.join(MODES)}): ").strip().lower()
                        if ans in MODES:
                            current_mode = ans
                            db.save_session(session_id, session_name, current_mode, current_autonomy, f"{current_provider}/{current_model}", current_target)
                            console.print(f"[green]Mode set to {current_mode}[/green]")
                        else:
                            console.print("[red]Invalid mode.[/red]")
                    elif arg in MODES:
                        current_mode = arg
                        db.save_session(session_id, session_name, current_mode, current_autonomy, f"{current_provider}/{current_model}", current_target)
                        console.print(f"[green]Mode set to {current_mode}[/green]")
                    else:
                        console.print(f"[red]Unknown mode: {arg}[/red]")
                    continue
                elif cmd == "model":
                    if not arg:
                        console.print(f"Current model: {current_provider}/{current_model}")
                        ans = input("Enter provider:model (e.g. openai:gpt-4): ").strip()
                        if ans:
                            arg = ans
                    if arg:
                        try:
                            from redforge.llm.base import ProviderFactory
                            prov, mod = current_provider, current_model
                            if ":" in arg:
                                prov, mod = arg.split(":", 1)
                            elif " " in arg:
                                prov, mod = arg.split(maxsplit=1)
                            else:
                                mod = arg
                            prov = prov.strip()
                            mod = mod.strip()
                            if prov not in ProviderFactory.list_providers():
                                console.print(f"[red]Unknown provider: {prov}[/red]")
                                continue
                            current_provider, current_model = prov, mod
                            rebuild_agent(current_provider, current_model)
                            db.save_session(session_id, session_name, current_mode, current_autonomy, f"{current_provider}/{current_model}", current_target)
                            console.print(f"[green]Model set to {current_provider}/{current_model}[/green]")
                        except Exception as e:
                            console.print(f"[red]Failed to switch model: {e}[/red]")
                    continue
                elif cmd == "target":
                    current_target = arg
                    db.save_session(session_id, session_name, current_mode, current_autonomy, f"{current_provider}/{current_model}", current_target)
                    console.print(f"[green]Target set to {arg or 'cleared'}[/green]")
                    continue
                elif cmd == "autonomy":
                    if not arg:
                        console.print(f"Current autonomy: {current_autonomy}")
                        ans = input("Select autonomy level (manual/partial/full): ").strip().lower()
                        if ans in ("manual", "partial", "full"):
                            arg = ans
                    if arg in ("manual", "partial", "full"):
                        current_autonomy = arg
                        autonomy_level = AutonomyLevel(current_autonomy)
                        autonomy_ctrl.set_level(autonomy_level)
                        db.save_session(session_id, session_name, current_mode, current_autonomy, f"{current_provider}/{current_model}", current_target)
                        console.print(f"[green]Autonomy set to {current_autonomy}[/green]")
                    else:
                        console.print(f"[red]Unknown autonomy level: {arg}[/red]")
                    continue
                elif cmd == "status":
                    _print_status(agent, autonomy_ctrl, loop_detector, prior_state)
                    continue
                elif cmd == "findings":
                    findings = db.get_findings(session_id)
                    if not findings:
                        console.print("[dim]No findings yet.[/dim]")
                    else:
                        t = Table(title=f"Findings ({len(findings)})", show_header=True, header_style="bold red")
                        t.add_column("#", style="dim", width=3)
                        t.add_column("Severity", style="bold")
                        t.add_column("Type")
                        t.add_column("Title")
                        sev_colors = {"critical": "red", "high": "bright_red", "medium": "yellow", "low": "blue", "info": "dim"}
                        for i, f in enumerate(findings, 1):
                            sev = f.get("severity", "info").lower()
                            color = sev_colors.get(sev, "white")
                            t.add_row(str(i), f"[{color}]{sev.upper()}[/{color}]", f.get("type", "?"), f.get("title", "")[:60])
                        console.print(t)
                    continue
                elif cmd == "files":
                    refresh_project_files()
                    if project_files:
                        console.print(f"[cyan]Project Root:[/cyan] {project_root}")
                        for path in project_files[:20]:
                            console.print(format_relpath(path))
                        if len(project_files) > 20:
                            console.print(f"  ... and {len(project_files) - 20} more.")
                    else:
                        console.print(f"[yellow]No files found under {project_root}[/yellow]")
                    continue
                elif cmd == "file":
                    if not arg:
                        console.print("[red]Usage: /file <path>[/red]")
                        continue
                    path = resolve_project_path(arg)
                    if not path.exists() or not path.is_file():
                        console.print(f"[red]File not found: {path}[/red]")
                    else:
                        if path not in attached_files:
                            attached_files.append(path)
                        console.print(f"[green]Attached {format_relpath(path)}[/green]")
                        db.add_message(
                            session_id=session_id,
                            role="system",
                            content=f"Attached {format_relpath(path)}"
                        )
                    continue
                elif cmd == "unfile":
                    if not arg:
                        console.print("[red]Usage: /unfile <path>[/red]")
                        continue
                    path = resolve_project_path(arg)
                    attached_files = [item for item in attached_files if item != path]
                    console.print(f"[green]Detached {format_relpath(path)}[/green]")
                    continue
                elif cmd == "cwd":
                    next_root = resolve_project_path(arg or ".")
                    if not next_root.exists() or not next_root.is_dir():
                        console.print(f"[red]Invalid directory: {next_root}[/red]")
                    else:
                        project_root = next_root
                        attached_files = [path for path in attached_files if path.exists()]
                        refresh_project_files()
                        console.print(f"[green]Project root set to {project_root}[/green]")
                    continue
                elif cmd == "session":
                    subparts = arg.split(maxsplit=1)
                    subcmd = subparts[0].lower() if subparts else "current"
                    val = subparts[1].strip() if len(subparts) > 1 else ""
                    
                    if subcmd == "list":
                        sessions = db.list_sessions()
                        console.print(f"[cyan]Saved Sessions ({len(sessions)}):[/cyan]")
                        for s in sessions:
                            console.print(f"  {s['id'][:8]} | {s['name']} | target={s.get('target') or 'none'} | accessed={s['last_accessed']}")
                    elif subcmd == "current":
                        console.print(f"[cyan]Current Session:[/cyan] {session_name} ({session_id})")
                        console.print(f"  Target: {current_target or 'not set'}")
                        console.print(f"  Mode: {current_mode}")
                        console.print(f"  Autonomy: {current_autonomy}")
                        console.print(f"  Model: {current_provider}/{current_model}")
                    elif subcmd == "save":
                        name = val or session_name
                        session_name = name
                        db.save_session(session_id, name, current_mode, current_autonomy, f"{current_provider}/{current_model}", current_target)
                        console.print(f"[green]Session saved successfully as '{name}'.[/green]")
                    elif subcmd == "load":
                        if not val:
                            console.print("[red]Usage: /session load <id_or_name>[/red]")
                            continue
                        target_id = None
                        for s in db.list_sessions():
                            if s["id"].startswith(val) or s["name"] == val:
                                target_id = s["id"]
                                break
                        if not target_id:
                            console.print(f"[red]Session not found matching '{val}'[/red]")
                            continue
                        loaded = db.load_session(target_id)
                        if loaded:
                            session_id = loaded["id"]
                            session_name = loaded["name"]
                            current_target = loaded.get("target") or ""
                            current_mode = loaded.get("mode") or "bugbounty"
                            current_autonomy = loaded.get("autonomy") or "manual"
                            db_model = loaded.get("model") or ""
                            if db_model and "/" in db_model:
                                current_provider, current_model = db_model.split("/", 1)
                                rebuild_agent(current_provider, current_model)
                            prior_state = _reconstruct_prior_state(db, session_id, workspace.id, workspace.name, current_target, current_mode, current_autonomy)
                            console.print(f"[green]Loaded session '{session_name}' ({session_id[:8]})[/green]")
                        else:
                            console.print(f"[red]Failed to load session '{val}'[/red]")
                    elif subcmd == "delete":
                        if not val:
                            console.print("[red]Usage: /session delete <id_or_name>[/red]")
                            continue
                        target_id = None
                        for s in db.list_sessions():
                            if s["id"].startswith(val) or s["name"] == val:
                                target_id = s["id"]
                                break
                        if not target_id:
                            console.print(f"[red]Session not found matching '{val}'[/red]")
                            continue
                        if db.delete_session(target_id):
                            console.print(f"[green]Deleted session '{val}'.[/green]")
                            if target_id == session_id:
                                session_id = str(uuid.uuid4())
                                session_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                prior_state = None
                                db.create_session(session_id, session_name, current_mode, current_autonomy, f"{current_provider}/{current_model}", current_target)
                                console.print("[green]Active session deleted. Started a new fresh session.[/green]")
                        else:
                            console.print(f"[red]Failed to delete session '{val}'[/red]")
                    elif subcmd == "export":
                        export_path = Path(val or f"session_{session_id}.json")
                        export_data = {
                            "id": session_id,
                            "name": session_name,
                            "target": current_target,
                            "mode": current_mode,
                            "autonomy": current_autonomy,
                            "messages": db.get_messages(session_id),
                            "findings": db.get_findings(session_id),
                            "tasks": db.get_tasks(session_id)
                        }
                        try:
                            with open(export_path, "w") as f:
                                json.dump(export_data, f, indent=2)
                            console.print(f"[green]Session successfully exported to {export_path.resolve()}[/green]")
                        except Exception as e:
                            console.print(f"[red]Export failed: {e}[/red]")
                    else:
                        console.print("[red]Unknown session subcommand. Supported: list, current, save, load, delete, export[/red]")
                    continue
                elif cmd == "report":
                    subparts = arg.split(maxsplit=1)
                    subcmd = subparts[0].lower() if subparts else "generate"
                    val = subparts[1].strip() if len(subparts) > 1 else ""
                    findings = db.get_findings(session_id)
                    
                    if subcmd == "generate":
                        if not findings:
                            console.print("[yellow]No findings in this session to report.[/yellow]")
                        else:
                            from redforge.advanced import ReportGenerator
                            rg = ReportGenerator()
                            report_findings = [{"title": f.get("title") or "Vulnerability Finding", "severity": f.get("severity") or "INFO", "cvss_score": 0.0, "cwe_id": "N/A", "description": f.get("description") or "", "impact": "Potential security compromise.", "remediation": "Review codebase and apply appropriate fix."} for f in findings]
                            report_data = {
                                "title": f"Security Assessment Report for {current_target or 'Unknown Target'}",
                                "target": current_target or "localhost",
                                "author": "RedForge CLI",
                                "scope": [current_target] if current_target else ["In-scope codebase"],
                                "findings": report_findings,
                                "summary": f"A total of {len(findings)} findings were identified during the assessment.",
                                "methodology": "Automated security review and analysis.",
                                "limitations": "Standard constraints of automated scanning."
                            }
                            rg.create_report(report_data, session_target=current_target)
                            report_dir = Path("workspaces") / "default" / "reports"
                            report_dir.mkdir(parents=True, exist_ok=True)
                            report_path = report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                            rg.save_report(report_path, format="md")
                            console.print(f"[green]Report successfully generated and saved to {report_path}[/green]")
                    elif subcmd == "export":
                        if not val:
                            console.print("[red]Usage: /report export <path>[/red]")
                            continue
                        from redforge.advanced import ReportGenerator
                        rg = ReportGenerator()
                        report_findings = [{"title": f.get("title") or "Vulnerability Finding", "severity": f.get("severity") or "INFO", "cvss_score": 0.0, "cwe_id": "N/A", "description": f.get("description") or "", "impact": "Potential security compromise.", "remediation": "Review codebase and apply appropriate fix."} for f in findings]
                        report_data = {
                            "title": f"Security Assessment Report for {current_target or 'Unknown Target'}",
                            "target": current_target or "localhost",
                            "author": "RedForge CLI",
                            "scope": [current_target] if current_target else ["In-scope codebase"],
                            "findings": report_findings,
                            "summary": f"A total of {len(findings)} findings were identified during the assessment.",
                            "methodology": "Automated security review and analysis.",
                            "limitations": "Standard constraints of automated scanning."
                        }
                        rg.create_report(report_data, session_target=current_target)
                        dest = Path(val)
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        rg.save_report(dest, format="md")
                        console.print(f"[green]Report successfully exported to {dest.resolve()}[/green]")
                    elif subcmd == "list":
                        report_dir = Path("workspaces") / "default" / "reports"
                        if report_dir.exists():
                            reports = list(report_dir.glob("*.md"))
                            if reports:
                                console.print("[cyan]Generated Reports:[/cyan]")
                                for r in reports:
                                    console.print(f"  {r.name}")
                            else:
                                console.print("[yellow]No reports found.[/yellow]")
                        else:
                            console.print("[yellow]No reports directory exists yet.[/yellow]")
                    else:
                        console.print("[red]Unknown report subcommand. Supported: generate, export, list[/red]")
                    continue
                elif cmd == "tools":
                    subparts = arg.split(maxsplit=1)
                    subcmd = subparts[0].lower() if subparts else "list"
                    val = subparts[1].strip() if len(subparts) > 1 else ""
                    from redforge.tools import ToolRegistry, ToolManager
                    tm = ToolManager()
                    
                    if subcmd == "list":
                        console.print("[cyan]RedForge Security Tools Registry:[/cyan]")
                        for name, tool in ToolRegistry.get_all_tools().items():
                            status = tm.check_tool(name)
                            status_str = f"Installed ({status.version})" if status.installed else "Not Installed"
                            console.print(f"  {name:<12} | {status_str:<15} | {tool.description}")
                    elif subcmd == "verify":
                        report = tm.get_status_report()
                        console.print(f"[green]Verification completed. Installed: {report['installed']}/{report['total_tools']} tools.[/green]")
                        for name, status in tm.installed_tools.items():
                            if not status.installed:
                                console.print(f"  [red][MISSING][/red] {name}")
                    elif subcmd == "install":
                        if not val:
                            console.print("[red]Usage: /tools install <tool_name>[/red]")
                            continue
                        console.print(f"Installing {val}...")
                        success, msg = tm.install_tool(val)
                        console.print(msg)
                    elif subcmd == "update":
                        console.print("Updating security tools...")
                        for name in tm.installed_tools:
                            status = tm.check_tool(name)
                            if status.installed:
                                console.print(f"Updating {name}...")
                                success, msg = tm.update_tool(name)
                                console.print(msg)
                    else:
                        console.print("[red]Unknown tools subcommand. Supported: list, verify, install, update[/red]")
                    continue
                elif cmd == "memory":
                    from redforge.memory.memory_manager import WorkspaceMemoryManager
                    mm = WorkspaceMemoryManager("default", settings.memory.persist_dir, settings.memory.vector_db)
                    subparts = arg.split(maxsplit=1)
                    subcmd = subparts[0].lower() if subparts else "stats"
                    val = subparts[1].strip() if len(subparts) > 1 else ""
                    
                    if subcmd == "stats":
                        stats = mm.get_stats()
                        console.print(f"Memory Stats: {stats.get('indexed_entries', 0)} entries, {stats.get('total_notes', 0)} notes, {stats.get('total_findings', 0)} findings.")
                    elif subcmd == "clear":
                        mm.clear()
                        console.print("[green]Workspace memory cleared successfully.[/green]")
                    elif subcmd == "rebuild":
                        console.print("Rebuilding vector store index...")
                        mm.clear()
                        messages = db.get_messages(session_id)
                        findings = db.get_findings(session_id)
                        for m in messages:
                            mm.add_session(m["role"], m["content"], {"timestamp": m.get("timestamp")})
                        for f in findings:
                            mm.add_finding(f["type"], f["title"], f["description"], f["severity"], f["target"], f.get("evidence"))
                        console.print("[green]Vector store index rebuilt successfully.[/green]")
                    elif subcmd == "search":
                        if not val:
                            console.print("[red]Usage: /memory search <query>[/red]")
                            continue
                        results = mm.search(val, limit=5)
                        if not results:
                            console.print(f"[yellow]No memory results found for '{val}'.[/yellow]")
                        else:
                            console.print(f"[cyan]Memory search results for '{val}':[/cyan]")
                            for idx, res in enumerate(results, 1):
                                console.print(f"{idx}. [score: {res.score:.2f}] {res.content}")
                    else:
                        console.print("[red]Unknown memory subcommand. Supported: stats, clear, rebuild, search[/red]")
                    continue
                elif cmd == "history":
                    messages = db.get_messages(session_id)
                    if not messages:
                        console.print("[dim]No history found in this session.[/dim]")
                    else:
                        console.print(f"[cyan]Session history ({len(messages)} items):[/cyan]")
                        for m in messages:
                            role, content = m["role"], m["content"]
                            if arg and arg.lower() not in content.lower():
                                continue
                            console.print(f"[{role.upper()}] {content[:100]}...")
                    continue
                elif cmd == "workspace":
                    subparts = arg.split(maxsplit=1)
                    subcmd = subparts[0].lower() if subparts else "info"
                    val = subparts[1].strip() if len(subparts) > 1 else ""
                    
                    if subcmd == "info":
                        console.print("[cyan]Workspace Info:[/cyan]")
                        console.print(f"  Root path: {project_root}")
                        console.print(f"  Tracked files: {len(project_files)}")
                        total_size = sum(f.stat().st_size for f in project_files if f.exists())
                        console.print(f"  Total size: {total_size / (1024*1024):.2f} MB")
                    elif subcmd == "files":
                        refresh_project_files()
                        if project_files:
                            console.print(f"[cyan]Workspace files ({len(project_files)}):[/cyan]")
                            for f in project_files[:20]:
                                console.print(f"  {format_relpath(f)}")
                            if len(project_files) > 20:
                                console.print(f"  ... and {len(project_files) - 20} more.")
                        else:
                            console.print("[yellow]No files found.[/yellow]")
                    elif subcmd == "reset":
                        attached_files.clear()
                        refresh_project_files()
                        db.clear_session_data(session_id)
                        prior_state = None
                        console.print("[green]Workspace and active session reset completed.[/green]")
                    else:
                        console.print("[red]Unknown workspace subcommand. Supported: info, files, reset[/red]")
                    continue
                elif cmd == "doctor":
                    from redforge.utils.platform import detect_platform, check_tool_available
                    platform_info = detect_platform()
                    console.print(Panel.fit("🩺 RedForge System Health Check"))
                    console.print(f"OS: {platform_info.os_name} {platform_info.os_version}")
                    console.print(f"Package Manager: {platform_info.package_manager.value}")
                    db_status = "OK" if Path(db.db_path).exists() else "Missing"
                    console.print(f"SQLite DB: {db_status} ({db.db_path})")
                    if agent and agent.llm:
                        llm_status = "Available" if await asyncio.to_thread(agent.llm.is_available) else "Unavailable"
                    else:
                        llm_status = "Unavailable"
                    console.print(f"LLM Provider ({current_provider}/{current_model}): {llm_status}")
                    from redforge.memory.memory_manager import WorkspaceMemoryManager
                    mm = WorkspaceMemoryManager("default", settings.memory.persist_dir, settings.memory.vector_db)
                    stats = mm.get_stats()
                    console.print(f"RAG Memory Store: {'Available' if stats.get('vector_store_available') else 'Unavailable'}")
                    tools_to_check = ["nmap", "ffuf", "sqlmap", "burpsuite", "gdb", "pwntools", "binwalk", "hashcat", "apktool", "git", "curl"]
                    console.print("Core Pentesting Tools Status:")
                    for tool in tools_to_check:
                        avail, path = check_tool_available(tool)
                        status_icon = "[green]✓[/green]" if avail else "[red]✗[/red]"
                        console.print(f"  {status_icon} {tool}: {path or 'not found'}")
                    continue
                elif cmd == "config":
                    from redforge.core.config import ConfigManager
                    cm = ConfigManager()
                    if not arg:
                        console.print(f"Current Settings:\n{json.dumps(cm.settings.model_dump(), indent=2)}")
                    else:
                        subparts = arg.split(maxsplit=1)
                        if len(subparts) == 2:
                            key, val = subparts[0], subparts[1]
                            if val.lower() == "true":
                                val = True
                            elif val.lower() == "false":
                                val = False
                            else:
                                try:
                                    val = float(val) if "." in val else int(val)
                                except ValueError:
                                    pass
                            cm.set(key, val)
                            console.print(f"[green]Set config {key} = {val}[/green]")
                        else:
                            val = cm.get(subparts[0])
                            console.print(f"Config {subparts[0]} = {val}")
                    continue
                elif cmd in ("approved", "approve"):
                    run_autonomy = AutonomyLevel.PARTIAL
                    run_input = "[APPROVED] Execute the planned action."
                else:
                    console.print(f"[red]Unknown command: {clean_input}[/red]")
                    continue

            else:
                run_autonomy = autonomy_ctrl.current_level
                run_input = user_input

            # Add message to SQLite
            db.add_message(
                session_id=session_id,
                role="user",
                content=run_input
            )

            # Print user message to terminal history
            console.print(f"\n[bold #ff4f00]▶ You[/bold #ff4f00]\n  {escape(run_input)}\n")

            # Inline render context
            active_block = ActiveBlock()
            active_block.mode = current_mode
            active_block.workspace = workspace.name
            
            with Live(active_block, console=console, refresh_per_second=15, transient=True) as live:
                # 1. Run agent task in background
                task = asyncio.create_task(agent.run(
                    user_input=build_message_with_file_context(run_input),
                    target=current_target,
                    workspace_id=workspace.id,
                    workspace_name=workspace.name,
                    autonomy_level=run_autonomy,
                    mode=agent_mode,
                    prior_state=prior_state,
                    active_mode=current_mode,
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

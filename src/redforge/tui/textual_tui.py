"""
RedForge TUI
Claude Code-style terminal UI built with Textual.
"""

from __future__ import annotations

import asyncio
import os
import re
import time
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from redforge.core.database import SessionDatabase

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Input, RichLog, Static

from redforge.tui.palette import (
    CommandPalette,
    CommandRegistry,
    ConfirmationModal,
    FileMentionScreen,
    ModelSelectionScreen,
    OptionSelectionScreen,
    ToastManager,
)
from redforge.tui.renderer import (
    ACCENT,
    BG,
    BG_PANEL,
    FG,
    FG_DIM,
    FG_MUTED,
    MODE_COLOR,
    MODE_LABEL,
    MODES,
    MessageRenderer,
    MessageStore,
    StreamQueue,
    osc_progress,
    osc_title,
)
from redforge.tui.widgets import FooterBar, SpinnerWidget, VimInput


class Sidebar(Static):
    """Minimal session sidebar."""

    DEFAULT_CSS = f"""
    Sidebar {{
        width: 30;
        min-width: 30;
        background: {BG_PANEL};
        border-right: tall {FG_DIM};
        color: {FG};
        padding: 1 1 1 2;
        transition: width 300ms in_out_cubic;
    }}
    Sidebar.hidden {{
        width: 0;
        min-width: 0;
        padding: 0;
        border-right: none;
    }}
    """

    def update_content(
        self,
        *,
        mode: str,
        autonomy: str,
        target: str,
        model: str,
        findings: int,
        messages: int,
        project_root: str,
        project_files: list[str],
        attached_files: list[str],
        tools_used: list[str] | None = None,
        memory_hits: int = 0,
    ) -> None:
        if tools_used is None:
            tools_used = []
            
        mc = MODE_COLOR.get(mode, ACCENT)
        target_text = target or "not set"
        
        # Stylized mini-logo for sidebar
        logo = (
            f"[bold {ACCENT}]  ██████╗ ███████╗\n"
            f"  ██╔══██╗██╔════╝\n"
            f"  ██████╔╝█████╗  \n"
            f"  ██╔══██╗██╔══╝  \n"
            f"  ██║  ██║███████╗\n"
            f"  ╚═╝  ╚═╝╚══════╝[/]\n"
            f"  [bold {FG}]REDFORGE[/] [dim]v0.2.0[/]"
        )
        
        lines = [
            logo,
            "",
            f"[{FG_MUTED}]Status[/]",
            f"[bold {mc}]●[/] {MODE_LABEL.get(mode, mode.upper())}",
            f"[{ACCENT}]●[/] {autonomy.upper()}",
            "",
            f"[{FG_MUTED}]Target[/]",
            f"[bold]{target_text}[/]",
            "",
            f"[{FG_MUTED}]Model[/]",
            f"{model}",
            "",
            f"[{FG_MUTED}]TOOLS[/]",
        ]

        if tools_used:
            for t in tools_used[-5:]:
                lines.append(f"  [{ACCENT}]✓[/] {t}")
        else:
            lines.append(f"  [dim]none[/]")

        lines.extend([
            "",
            f"[{FG_MUTED}]MEMORY[/]",
            f"  {memory_hits} recent hits",
            "",
            f"[{FG_MUTED}]Session Stats[/]",
            f"[{ACCENT}]▸[/] {messages} messages",
            f"[{ACCENT}]▸[/] {findings} findings",
            "",
            f"[{FG_MUTED}]Attached Context[/]",
        ])
        
        if attached_files:
            for f in attached_files[:5]:
                lines.append(f"  [#00d4ff]@{f}[/]")
        else:
            lines.append("  [dim]none[/]")
            
        lines.extend([
            "",
            f"[{FG_MUTED}]Shortcuts[/]",
            f"[{ACCENT}]Tab[/]     Palette",
            f"[{ACCENT}]Ctrl+B[/]  Sidebar",
            f"[{ACCENT}]Ctrl+K[/]  Cancel",
            f"[{ACCENT}]Esc[/]     Focus",
        ])
        self.update("\n".join(lines))


class RedForgeTUI(App):
    """Claude Code-style RedForge TUI."""

    CSS = f"""
    Screen {{
        background: {BG};
        color: {FG};
    }}
    #layout {{
        layout: horizontal;
        height: 1fr;
    }}
    #main {{
        layout: vertical;
        width: 1fr;
    }}
    #header {{
        height: 3;
        padding: 0 2;
        background: {BG};
        border-bottom: tall {FG_DIM};
    }}
    #header-title {{
        color: {FG};
        text-style: bold;
    }}
    #header-subtitle {{
        color: {FG_MUTED};
    }}
    #transcript {{
        height: 1fr;
        background: {BG};
        padding: 0 1;
    }}
    #out-log {{
        padding: 1 2;
        background: {BG_PANEL};
        border: tall {FG_DIM};
    }}
    #spinner-wrap {{
        height: auto;
        display: none;
        background: {BG};
        padding: 0 1;
    }}
    #spinner-wrap.active {{
        display: block;
    }}
    .hidden {{
        display: none;
    }}
    #sidebar.hidden {{
        display: block;
    }}
    """

    BINDINGS = [
        Binding("ctrl+b", "toggle_sidebar", "Sidebar"),
        Binding("ctrl+l", "clear_output", "Clear"),
        Binding("f2", "cycle_mode", "Mode"),
        Binding("ctrl+k", "kill_task", "Cancel"),
        Binding("escape", "focus_input", "Input"),
    ]

    mode: reactive[str] = reactive("bugbounty")
    tokens: reactive[int] = reactive(0)
    latency: reactive[float] = reactive(0.0)
    autonomy: reactive[str] = reactive("manual")
    target: reactive[str] = reactive("")
    model_label: reactive[str] = reactive("offline")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = MessageStore(max_messages=1000)
        self.stream = StreamQueue(chars_per_tick=8)
        self.renderer = MessageRenderer(self.store, self.stream, "bugbounty")
        self.toast_mgr = ToastManager()

        self.db = SessionDatabase()
        self.session_id = str(uuid.uuid4())
        self.session_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.store.on_append = self._on_message_appended

        self._agent = None
        self._prior_state = None
        self._agent_task: Optional[asyncio.Task] = None
        self._sidebar_visible = True
        self._project_root = Path.cwd()
        self._project_files: list[Path] = []
        self._attached_files: list[Path] = []
        self._live_agent_events = False
        self._confirmation_announced = False

    def _on_message_appended(self, msg) -> None:
        self.db.add_message(
            session_id=self.session_id,
            role=msg.role,
            content=msg.content,
            tool_name=msg.tool_name,
            command=msg.command,
            severity=msg.severity,
            status=msg.status,
            duration_s=msg.duration_s,
            timestamp=msg.timestamp
        )
        if msg.role == "finding":
            finding_id = msg.tool_name if msg.tool_name else str(uuid.uuid4())
            self.db.add_finding(
                session_id=self.session_id,
                id=finding_id,
                type=msg.tool_name or "finding",
                title="Vulnerability Finding",
                description=msg.content,
                severity=msg.severity or "medium",
                target=self.target,
                evidence=None
            )

    def compose(self) -> ComposeResult:
        with Horizontal(id="layout"):
            yield Sidebar(id="sidebar")
            with Vertical(id="main"):
                with Vertical(id="header"):
                    yield Static("RedForge", id="header-title")
                    yield Static("", id="header-subtitle")
                with ScrollableContainer(id="transcript"):
                    yield RichLog(id="out-log", markup=True, highlight=True, wrap=True, auto_scroll=True)
                with Vertical(id="spinner-wrap"):
                    yield SpinnerWidget(id="spinner")
                yield VimInput(id="vim-input")
                yield FooterBar(id="footer")
        yield self.toast_mgr

    async def on_mount(self) -> None:
        self._render_header()
        self._sync_chrome()
        self.renderer.feed_system("RedForge terminal ready.")
        self.renderer.feed_system("Use /help for commands, !shell for local commands, and @file mentions for project files.")
        self.load_previous_session()
        self._refresh_project_files()
        self._refresh_transcript()
        self.set_interval(0.08, self._tick_spinner)
        self.set_interval(5.0, self._refresh_project_files)
        self.call_later(self._init_agent)
        osc_title(f"RedForge [{self.mode}]")

    def load_previous_session(self) -> None:
        latest = self.db.list_sessions()
        if latest:
            last_sess = latest[0]
            success = self._load_session_state(last_sess["id"])
            if success:
                findings_count = len(self.db.get_findings(self.session_id))
                open_tasks = [t for t in self.db.get_tasks(self.session_id) if t["status"] in ("pending", "in_progress")]
                self.renderer.feed_system(f"Last Session: {self.session_name} ({self.session_id[:8]})")
                self.renderer.feed_system(f"Last Target: {self.target or 'not set'}")
                self.renderer.feed_system(f"Last Findings: {findings_count}")
                self.renderer.feed_system(f"Open Tasks: {len(open_tasks)}")
                if open_tasks:
                    for t in open_tasks:
                        self.renderer.feed_system(f"  - [ ] {t['description']}")
                self.renderer.feed_system("Continuity Check: Resumed last session. To start a new session, use /session load or /session delete.")
                return

        # Start fresh session
        self.db.create_session(self.session_id, self.session_name, self.mode, self.autonomy, self.model_label, self.target)
        self.renderer.feed_system(f"Starting fresh session: {self.session_name} ({self.session_id[:8]})")

    def _load_session_state(self, session_id: str) -> bool:
        session = self.db.load_session(session_id)
        if not session:
            return False
        self.session_id = session["id"]
        self.session_name = session["name"]
        self.target = session.get("target") or ""
        self.mode = session.get("mode") or "bugbounty"
        self.autonomy = session.get("autonomy") or "manual"
        # Restore messages
        self.store.clear()
        old_on_append = self.store.on_append
        self.store.on_append = None
        try:
            from redforge.tui.renderer import Msg
            for m in self.db.get_messages(session_id):
                msg = Msg(
                    role=m["role"],
                    content=m["content"],
                    tool_name=m.get("tool_name") or "",
                    command=m.get("command") or "",
                    severity=m.get("severity") or "",
                    status=m.get("status") or "",
                    duration_s=m.get("duration_s") or 0.0,
                    timestamp=m.get("timestamp") or time.time()
                )
                self.store.append(msg)
        finally:
            self.store.on_append = old_on_append
        return True

    def _init_agent(self) -> None:
        try:
            from redforge.core.config import get_settings

            settings = get_settings()
            self._rebuild_agent(settings.llm.provider, settings.llm.model, announce=False)
            self.toast_mgr.show("Agent connected", "success")
        except Exception as exc:
            self.model_label = "agent unavailable"
            self.renderer.feed_error(f"Agent unavailable: {exc}")
            self._refresh_transcript()

    def _rebuild_agent(self, provider: str, model: str, announce: bool = True) -> None:
        from redforge.core.config import get_settings
        from redforge.core.langgraph_agent import RedForgeAgent

        settings = get_settings()
        settings.llm.provider = provider
        settings.llm.model = model
        self._agent = RedForgeAgent(
            config=settings,
            llm_provider=provider,
            model=model,
            api_key=settings.llm.api_key,
            base_url=settings.llm.base_url,
        )
        self._bind_agent_events()
        self.model_label = f"{provider}/{model}"
        self._prior_state = None
        if announce:
            self.renderer.feed_system(f"LLM set to {self.model_label}")

    def _on_agent_finding(self, payload: dict) -> None:
        finding = payload.get("finding", {})
        self.toast_mgr.show(f"New finding: {finding.get('title')}", "success")
        self._refresh_transcript()

    def _bind_agent_events(self) -> None:
        if not self._agent:
            return
        self._agent.on("assistant_start", self._on_agent_assistant_start)
        self._agent.on("token", self._on_agent_token)
        self._agent.on("assistant_end", self._on_agent_assistant_end)
        self._agent.on("tool_start", self._on_agent_tool_start)
        self._agent.on("tool_end", self._on_agent_tool_end)
        self._agent.on("finding", self._on_agent_finding)
        self._agent.on("confirmation_required", self._on_agent_confirmation_required)
        self._agent.on("error", self._on_agent_error)

    def _on_agent_assistant_start(self, payload: dict) -> None:
        self._live_agent_events = True
        self.renderer.start_assistant()
        self._refresh_transcript()

    def _on_agent_token(self, payload: dict) -> None:
        self._live_agent_events = True
        chunk = payload.get("content", "")
        if chunk:
            self.renderer.append_assistant_chunk(chunk)
            self._refresh_transcript()

    def _on_agent_assistant_end(self, payload: dict) -> None:
        self._live_agent_events = True
        self.renderer.finish_assistant(payload.get("content"))
        self.tokens += int(payload.get("total_tokens", 0) or 0)
        self._refresh_transcript()

    def _on_agent_tool_start(self, payload: dict) -> None:
        self._live_agent_events = True
        self.renderer.start_tool(
            payload.get("call_id", ""),
            payload.get("tool", "tool"),
            payload.get("command", ""),
        )
        self._refresh_transcript()

    def _on_agent_tool_end(self, payload: dict) -> None:
        self._live_agent_events = True
        result = payload.get("result", {}) or {}
        self.renderer.finish_tool(
            payload.get("call_id", ""),
            output=result.get("output") or payload.get("error") or "(no output)",
            status="done" if payload.get("success") else "failed",
            duration_s=float(result.get("duration_s", 0.0) or 0.0),
            tool_name=payload.get("tool", "tool"),
            command=payload.get("command", ""),
        )
        self._refresh_transcript()

    def _on_agent_confirmation_required(self, payload: dict) -> None:
        self._live_agent_events = True
        pending = payload.get("pending_confirmation", {})
        msg = pending.get("message", "The agent is requesting approval for a tool action.")
        
        # Get command string for display
        cmd_str = ""
        calls = pending.get("tool_calls", [])
        if calls:
            cmd_str = calls[0].get("command") or calls[0].get("code") or str(calls[0])

        if not self._confirmation_announced:
            self.renderer.feed_system(f"Approval Required: {msg}")
            self._confirmation_announced = True
            self._refresh_transcript()
        
        # Trigger modal
        self.push_screen(ConfirmationModal(msg, cmd_str), self._handle_approval_result)

    def _handle_approval_result(self, approved: bool | None) -> None:
        if approved:
            self.toast_mgr.show("Action approved", "success")
            asyncio.create_task(self._chat("[APPROVED] Execute the planned action."))
        else:
            self.toast_mgr.show("Action rejected", "warning")
            asyncio.create_task(self._chat("Cancel tool execution. Do not run this command."))

    def _on_agent_error(self, payload: dict) -> None:
        self.renderer.feed_error(payload.get("message", "Agent error"))
        self._refresh_transcript()

    async def _list_models_for_provider(self, provider: str, api_key: str = "") -> list[str]:
        from redforge.core.config import get_settings
        from redforge.llm.base import ProviderFactory
        from redforge.llm.catalog import DEFAULT_MODELS, FALLBACK_MODELS, resolve_api_key

        settings = get_settings()
        provider_api_key = resolve_api_key(provider, api_key or settings.llm.api_key)
        base_url = settings.llm.base_url if provider == "ollama" else ""
        try:
            provider_client = ProviderFactory.create(
                provider=provider,
                model=DEFAULT_MODELS.get(provider, settings.llm.model),
                api_key=provider_api_key,
                base_url=base_url,
                temperature=settings.llm.temperature,
                max_tokens=settings.llm.max_tokens,
            )
            return await asyncio.wait_for(provider_client.list_models(), timeout=2.5)
        except Exception:
            return FALLBACK_MODELS.get(provider, [])

    def _persist_llm_settings(self, provider: str, model: str, api_key: str) -> None:
        from redforge.core.config import find_config_file, get_settings, save_config

        settings = get_settings()
        settings.llm.provider = provider
        settings.llm.model = model
        settings.llm.api_key = api_key
        if provider == "ollama" and not settings.llm.base_url:
            settings.llm.base_url = "http://localhost:11434"

        config_path = find_config_file()
        if not config_path:
            # Fall back to user's home config directory to ensure it's globally persistent
            config_path = Path.home() / ".config" / "redforge" / "config.yaml"

        save_config(settings, config_path)

    def _parse_model_arg(self, arg: str) -> tuple[str, str]:
        from redforge.core.config import get_settings

        settings = get_settings()
        provider = settings.llm.provider
        model = settings.llm.model
        value = arg.strip()
        if not value:
            return provider, model

        if ":" in value:
            new_provider, new_model = value.split(":", 1)
            return new_provider.strip(), new_model.strip()

        parts = value.split(maxsplit=1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()

        return provider, value

    def _sync_session_meta(self) -> None:
        if hasattr(self, "db") and hasattr(self, "session_id"):
            self.db.save_session(
                self.session_id,
                self.session_name,
                self.mode,
                self.autonomy,
                self.model_label,
                self.target
            )

    def watch_mode(self, mode: str) -> None:
        if not hasattr(self, "renderer"):
            return
        self._refresh_project_files()
        self.renderer.mode = mode
        self.store.set_mode(mode)
        self._render_header()
        self._sync_chrome()
        osc_title(f"RedForge [{mode}]")
        self._sync_session_meta()

    def watch_autonomy(self, autonomy: str) -> None:
        if not hasattr(self, "store"):
            return
        self._render_header()
        self._sync_chrome()
        self._sync_session_meta()

    def watch_target(self, target: str) -> None:
        if not hasattr(self, "store"):
            return
        self._render_header()
        self._sync_chrome()
        self._sync_session_meta()

    def watch_model_label(self, model_label: str) -> None:
        if not hasattr(self, "store"):
            return
        self._sync_chrome()
        self._sync_session_meta()

    def watch_tokens(self, tokens: int) -> None:
        if not hasattr(self, "store"):
            return
        self._sync_chrome()

    def watch_latency(self, latency: float) -> None:
        if not hasattr(self, "store"):
            return
        self._sync_chrome()

    def _render_header(self) -> None:
        mc = MODE_COLOR.get(self.mode, ACCENT)
        subtitle = (
            f"[bold {mc}]{MODE_LABEL.get(self.mode, self.mode.upper())}[/]"
            f"  [{FG_MUTED}]autonomy[/] {self.autonomy}"
        )
        if self.target:
            subtitle += f"  [{FG_MUTED}]target[/] {self.target}"
        try:
            self.query_one("#header-title", Static).update(f"[bold {ACCENT}]RedForge[/]")
            self.query_one("#header-subtitle", Static).update(subtitle)
        except NoMatches:
            pass

    def _refresh_project_files(self) -> None:
        if getattr(self, "_is_refreshing", False):
            return
        self._is_refreshing = True

        def scan_files() -> list[Path]:
            files: list[Path] = []
            ignored = {".git", "__pycache__", ".venv", "venv", "node_modules", "dist", "build"}
            root = self._project_root
            if not root.exists():
                return []

            for current_root, dirs, names in os.walk(root):
                dirs[:] = [name for name in dirs if name not in ignored and not name.startswith(".")]
                for name in sorted(names):
                    if name.startswith("."):
                        continue
                    files.append(Path(current_root) / name)
            return files

        async def do_refresh():
            try:
                files = await asyncio.to_thread(scan_files)
                self._project_files = files
                logger.debug(f"Files Indexed: {len(files)} files found in {self._project_root}")
                self._sync_chrome()
            except Exception as e:
                logger.error(f"Failed to index files: {e}")
            finally:
                self._is_refreshing = False

        asyncio.create_task(do_refresh())

    def _resolve_project_path(self, raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = self._project_root / path
        return path.resolve()

    def _format_relpath(self, path: Path) -> str:
        try:
            return str(path.relative_to(self._project_root))
        except Exception:
            return str(path)

    def _read_file_context(self, path: Path, limit: int = 3000) -> str:
        try:
            data = path.read_bytes()
        except Exception as exc:
            return f"{self._format_relpath(path)}: failed to read ({exc})"

        metadata = f"Path: {self._format_relpath(path)} | Ext: {path.suffix or 'none'} | Dir: {self._format_relpath(path.parent)}"

        if b"\x00" in data[:512]:
            preview = data[:32].hex()
            return f"FILE METADATA: {metadata} | Type: binary | Size: {len(data)} bytes\nCONTENT PREVIEW: {preview}"

        text = data.decode("utf-8", errors="replace")
        trimmed = text[:limit]
        if len(text) > limit:
            trimmed += "\n[TRUNCATED]"
        return f"FILE METADATA: {metadata}\nCONTENT:\n{trimmed}"

    def _extract_mentioned_paths(self, message: str) -> list[Path]:
        paths: list[Path] = []
        seen: set[Path] = set()
        for match in re.finditer(r"@([^\s]+)", message):
            raw = match.group(1).rstrip(".,:;!?)]}")
            if not raw:
                continue
            path = self._resolve_project_path(raw)
            if path.exists() and path not in seen:
                seen.add(path)
                paths.append(path)
        return paths

    def _build_message_with_file_context(self, message: str) -> str:
        mentioned = self._extract_mentioned_paths(message)
        combined: list[Path] = []
        seen: set[Path] = set()
        for path in [*mentioned, *self._attached_files]:
            if path.exists() and path not in seen:
                seen.add(path)
                combined.append(path)
        if not combined:
            return message

        file_context = "\n\n".join(self._read_file_context(path) for path in combined[:6])
        return (
            f"{message}\n\n"
            f"Project file context from {self._project_root}:\n"
            f"{file_context}\n"
        )

    def _project_entries(self) -> list[str]:
        entries = [self._format_relpath(path) for path in self._project_files]
        attached = [self._format_relpath(path) for path in self._attached_files]
        ordered = [*attached, *entries]
        seen: set[str] = set()
        unique: list[str] = []
        for item in ordered:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        return unique

    def _sync_chrome(self) -> None:
        try:
            vim = self.query_one(VimInput)
            vim.app_mode = self.mode
            vim.tokens = self.tokens

            footer = self.query_one(FooterBar)
            footer.mode = self.mode
            footer.model = self.model_label
            footer.tokens = self.tokens
            footer.latency_ms = self.latency

            self.query_one(Sidebar).update_content(
                mode=self.mode,
                autonomy=self.autonomy,
                target=self.target,
                model=self.model_label,
                findings=len([m for m in self.store._msgs if m.role == "finding"]),
                messages=self.store.total,
                project_root=str(self._project_root),
                project_files=[self._format_relpath(path) for path in self._project_files],
                attached_files=[self._format_relpath(path) for path in self._attached_files],
                tools_used=[m.tool_name for m in self.store._msgs if m.role == "tool" and m.tool_name],
                memory_hits=len([m for m in self.store._msgs if "memory" in m.content.lower()]),
            )
        except NoMatches:
            pass

    def _refresh_transcript(self) -> None:
        try:
            log = self.query_one("#out-log", RichLog)
            log.clear()
            for block in self.store.all_rendered():
                log.write(block)
            self.query_one("#transcript", ScrollableContainer).scroll_end(animate=False)
        except NoMatches:
            pass
        self._sync_chrome()

    def _tick_spinner(self) -> None:
        try:
            self.query_one("#spinner", SpinnerWidget).tick()
        except NoMatches:
            pass

    def _set_spinner(self, active: bool, label: str = "thinking…") -> None:
        try:
            wrap = self.query_one("#spinner-wrap")
            spinner = self.query_one("#spinner", SpinnerWidget)
            spinner.label = label
            spinner.active = active
            if active:
                wrap.add_class("active")
            else:
                wrap.remove_class("active")
        except NoMatches:
            pass

    async def on_key(self, event) -> None:
        vim = self.query_one(VimInput)
        if event.key in ("up", "down") and not vim.value:
            vim.set_value(vim.recall_prev() if event.key == "up" else vim.recall_next())
            event.prevent_default()

    def _execute_palette_cmd(self, command: str) -> None:
        try:
            vim = self.query_one(VimInput)
            vim.set_value(command)
            vim.focus_input()
        except NoMatches:
            pass

    def open_command_palette(self, initial_query: str = "") -> None:
        if self.query(CommandPalette):
            return
        palette = CommandPalette(initial_query=initial_query)
        palette.on_select = self._execute_palette_cmd
        self.mount(palette)

    def open_file_mention_picker(self, query: str = "") -> None:
        self.push_screen(
            FileMentionScreen(files=self._project_entries(), query=query),
            self._handle_file_mention,
        )

    @on(Input.Submitted, "#vi-input")
    async def on_submit(self, event: Input.Submitted) -> None:
        await self._submit_input(event.value)

    @on(VimInput.Submitted)
    async def on_vim_submit(self, event: VimInput.Submitted) -> None:
        await self._submit_input(event.value)

    async def _submit_input(self, value: str) -> None:
        raw = value.strip()
        if not raw:
            return

        vim = self.query_one(VimInput)
        vim.push_history(raw)
        vim.clear_input()

        if raw.startswith("/"):
            await self._slash(raw)
        elif raw.startswith("!"):
            await self._shell(raw[1:].strip())
        else:
            await self._chat(raw)

    async def _slash(self, raw: str) -> None:
        parts = raw[1:].split(maxsplit=1)
        cmd = parts[0].lower() if parts else ""
        arg = parts[1].strip() if len(parts) > 1 else ""

        clean_raw = raw.strip()
        
        # Check command registry to verify if command exists
        if not CommandRegistry.exists(clean_raw):
            base_cmd = f"/{cmd}"
            if not CommandRegistry.exists(base_cmd):
                logger.error(f"Command Failed: {clean_raw}. Reason: Command does not exist in registry.")
                error_msg = f"Command Failed\nReason: Command {clean_raw} does not exist\nSuggested Fix: Use /help to see all available commands."
                self.renderer.feed_error(error_msg)
                self._refresh_transcript()
                return

        try:
            if cmd == "help":
                all_cmds = sorted([c["cmd"] for c in CommandRegistry.get_commands()])
                self.renderer.feed_system(f"Available Commands: {' '.join(all_cmds)}")
                self.renderer.feed_system("Type @ and start typing to insert project files into any prompt.")
            elif cmd == "clear":
                self.store.clear()
            elif cmd == "approved":
                await self._chat("[APPROVED] Execute the planned action.")
            elif cmd == "exit":
                self.exit()
            elif cmd == "config":
                from redforge.core.config import ConfigManager
                cm = ConfigManager()
                if not arg:
                    self.renderer.feed_system(f"Current Settings:\n{json.dumps(cm.settings.model_dump(), indent=2)}")
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
                        self.renderer.feed_system(f"Set config {key} = {val}")
                    else:
                        val = cm.get(subparts[0])
                        self.renderer.feed_system(f"Config {subparts[0]} = {val}")
            elif cmd == "doctor":
                from redforge.utils.platform import detect_platform, check_tool_available
                platform_info = detect_platform()
                self.renderer.feed_system("🩺 RedForge System Health Check")
                self.renderer.feed_system(f"OS: {platform_info.os_name} {platform_info.os_version}")
                self.renderer.feed_system(f"Package Manager: {platform_info.package_manager.value}")
                
                # SQLite check
                db_status = "OK" if Path(self.db.db_path).exists() else "Missing"
                self.db._init_db()
                self.renderer.feed_system(f"SQLite DB: {db_status} ({self.db.db_path})")
                
                # LLM check
                if self._agent and self._agent.llm:
                    llm_status = "Available" if await asyncio.to_thread(self._agent.llm.is_available) else "Unavailable"
                else:
                    llm_status = "Unavailable"
                self.renderer.feed_system(f"LLM Provider ({self.model_label}): {llm_status}")
                
                # Memory Check
                from redforge.core.config import get_settings
                from redforge.memory.memory_manager import WorkspaceMemoryManager
                settings = get_settings()
                mm = WorkspaceMemoryManager("default", settings.memory.persist_dir, settings.memory.vector_db)
                stats = mm.get_stats()
                self.renderer.feed_system(f"RAG Memory Store: {'Available' if stats.get('vector_store_available') else 'Unavailable'}")
                
                # Tools check
                tools_to_check = ["nmap", "ffuf", "sqlmap", "burpsuite", "gdb", "pwntools", "binwalk", "hashcat", "apktool", "git", "curl"]
                self.renderer.feed_system("Core Pentesting Tools Status:")
                for tool in tools_to_check:
                    avail, path = check_tool_available(tool)
                    status_icon = "✓" if avail else "✗"
                    self.renderer.feed_system(f"  [{status_icon}] {tool}: {path or 'not found'}")
            elif cmd == "workspace":
                subparts = arg.split(maxsplit=1)
                sub = subparts[0].lower() if subparts else ""
                val = subparts[1].strip() if len(subparts) > 1 else ""
                if not sub:
                    sub = "info"
                
                if sub == "info":
                    self.renderer.feed_system("Workspace Info:")
                    self.renderer.feed_system(f"  Root path: {self._project_root}")
                    self.renderer.feed_system(f"  Tracked files: {len(self._project_files)}")
                    total_size = sum(f.stat().st_size for f in self._project_files if f.exists())
                    self.renderer.feed_system(f"  Total size: {total_size / (1024*1024):.2f} MB")
                elif sub == "files":
                    self._refresh_project_files()
                    if self._project_files:
                        self.renderer.feed_system(f"Workspace files ({len(self._project_files)}):")
                        for f in self._project_files[:20]:
                            self.renderer.feed_system(f"  {self._format_relpath(f)}")
                        if len(self._project_files) > 20:
                            self.renderer.feed_system(f"  ... and {len(self._project_files) - 20} more.")
                    else:
                        self.renderer.feed_system("No files found.")
                elif sub == "reset":
                    self.store.clear()
                    self._attached_files.clear()
                    self._refresh_project_files()
                    self.db.clear_session_data(self.session_id)
                    self.renderer.feed_system("Workspace and active session reset completed.")
                else:
                    raise ValueError(f"Unknown workspace subcommand: {sub}")
            elif cmd == "history":
                messages = self.db.get_messages(self.session_id)
                if not messages:
                    self.renderer.feed_system("No history found in this session.")
                else:
                    self.renderer.feed_system(f"Session history ({len(messages)} items):")
                    for m in messages:
                        role, content = m["role"], m["content"]
                        if arg and arg.lower() not in content.lower():
                            continue
                        self.renderer.feed_system(f"[{role.upper()}] {content[:100]}...")
            elif cmd == "tools":
                subparts = arg.split(maxsplit=1)
                sub = subparts[0].lower() if subparts else ""
                val = subparts[1].strip() if len(subparts) > 1 else ""
                if not sub:
                    sub = "list"
                
                if sub == "list":
                    from redforge.tools import ToolRegistry, ToolManager
                    tm = ToolManager()
                    self.renderer.feed_system("RedForge Security Tools Registry:")
                    for name, tool in ToolRegistry.get_all_tools().items():
                        status = tm.check_tool(name)
                        status_str = f"Installed ({status.version})" if status.installed else "Not Installed"
                        self.renderer.feed_system(f"  {name:<12} | {status_str:<15} | {tool.description}")
                elif sub == "verify":
                    from redforge.tools import ToolManager
                    tm = ToolManager()
                    report = tm.get_status_report()
                    self.renderer.feed_system(f"Verification completed. Installed: {report['installed']}/{report['total_tools']} tools.")
                    for name, status in tm.installed_tools.items():
                        if not status.installed:
                            self.renderer.feed_system(f"  [MISSING] {name}")
                elif sub == "install":
                    if not val:
                        raise ValueError("Usage: /tools install <tool_name>")
                    from redforge.tools import ToolManager
                    tm = ToolManager()
                    self.renderer.feed_system(f"Installing {val}...")
                    success, msg = tm.install_tool(val)
                    self.renderer.feed_system(msg)
                elif sub == "update":
                    from redforge.tools import ToolManager
                    tm = ToolManager()
                    self.renderer.feed_system("Updating security tools...")
                    for name in tm.installed_tools:
                        status = tm.check_tool(name)
                        if status.installed:
                            self.renderer.feed_system(f"Updating {name}...")
                            success, msg = tm.update_tool(name)
                            self.renderer.feed_system(msg)
                else:
                    raise ValueError(f"Unknown tools subcommand: {sub}")
            elif cmd == "report":
                subparts = arg.split(maxsplit=1)
                sub = subparts[0].lower() if subparts else ""
                val = subparts[1].strip() if len(subparts) > 1 else ""
                if not sub:
                    sub = "generate"
                
                if sub == "generate":
                    findings = [m for m in self.store._msgs if m.role == "finding"]
                    if not findings:
                        self.renderer.feed_system("No findings in this session to report.")
                    else:
                        from redforge.advanced import ReportGenerator
                        rg = ReportGenerator()
                        report_findings = [{"title": "Vulnerability Finding", "severity": f.severity or "INFO", "cvss_score": 0.0, "cwe_id": "N/A", "description": f.content, "impact": "Potential security compromise.", "remediation": "Review codebase and apply appropriate fix."} for f in findings]
                        report_data = {
                            "title": f"Security Assessment Report for {self.target or 'Unknown Target'}",
                            "target": self.target or "localhost",
                            "author": "RedForge TUI",
                            "scope": [self.target] if self.target else ["In-scope codebase"],
                            "findings": report_findings,
                            "summary": f"A total of {len(findings)} findings were identified during the assessment.",
                            "methodology": "Automated security review and analysis.",
                            "limitations": "Standard constraints of automated scanning."
                        }
                        rg.create_report(report_data)
                        report_dir = Path("workspaces") / "default" / "reports"
                        report_dir.mkdir(parents=True, exist_ok=True)
                        report_path = report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                        rg.save_report(report_path, format="md")
                        self.renderer.feed_system(f"Report successfully generated and saved to {report_path}")
                elif sub == "export":
                    if not val:
                        raise ValueError("Usage: /report export <path>")
                    findings = [m for m in self.store._msgs if m.role == "finding"]
                    from redforge.advanced import ReportGenerator
                    rg = ReportGenerator()
                    report_findings = [{"title": "Vulnerability Finding", "severity": f.severity or "INFO", "cvss_score": 0.0, "cwe_id": "N/A", "description": f.content, "impact": "Potential security compromise.", "remediation": "Review codebase and apply appropriate fix."} for f in findings]
                    report_data = {
                        "title": f"Security Assessment Report for {self.target or 'Unknown Target'}",
                        "target": self.target or "localhost",
                        "author": "RedForge TUI",
                        "scope": [self.target] if self.target else ["In-scope codebase"],
                        "findings": report_findings,
                        "summary": f"A total of {len(findings)} findings were identified during the assessment.",
                        "methodology": "Automated security review and analysis.",
                        "limitations": "Standard constraints of automated scanning."
                    }
                    rg.create_report(report_data)
                    dest = Path(val)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    rg.save_report(dest, format="md")
                    self.renderer.feed_system(f"Report successfully exported to {dest.resolve()}")
                elif sub == "list":
                    report_dir = Path("workspaces") / "default" / "reports"
                    if report_dir.exists():
                        reports = list(report_dir.glob("*.md"))
                        if reports:
                            self.renderer.feed_system("Generated Reports:")
                            for r in reports:
                                self.renderer.feed_system(f"  {r.name}")
                        else:
                            self.renderer.feed_system("No reports found.")
                    else:
                        self.renderer.feed_system("No reports directory exists yet.")
                else:
                    raise ValueError(f"Unknown report subcommand: {sub}")
            elif cmd == "session":
                subparts = arg.split(maxsplit=1)
                sub = subparts[0].lower() if subparts else ""
                val = subparts[1].strip() if len(subparts) > 1 else ""
                if not sub:
                    sub = "current"
                
                if sub == "list":
                    sessions = self.db.list_sessions()
                    self.renderer.feed_system(f"Saved Sessions ({len(sessions)}):")
                    for s in sessions:
                        self.renderer.feed_system(f"  {s['id'][:8]} | {s['name']} | target={s.get('target') or 'none'} | accessed={s['last_accessed']}")
                elif sub == "save":
                    name = val or self.session_name
                    self.db.save_session(self.session_id, name, self.mode, self.autonomy, self.model_label, self.target)
                    self.renderer.feed_system(f"Session saved successfully as '{name}'.")
                elif sub == "load":
                    if not val:
                        raise ValueError("Usage: /session load <id>")
                    target_id = None
                    for s in self.db.list_sessions():
                        if s["id"].startswith(val) or s["name"] == val:
                            target_id = s["id"]
                            break
                    if not target_id:
                        raise ValueError(f"Session not found matching '{val}'")
                    success = self._load_session_state(target_id)
                    if success:
                        self.renderer.feed_system(f"Resumed session '{self.session_name}' ({self.session_id[:8]})")
                    else:
                        raise RuntimeError(f"Failed to load session state for '{val}'")
                elif sub == "delete":
                    if not val:
                        raise ValueError("Usage: /session delete <id>")
                    target_id = None
                    for s in self.db.list_sessions():
                        if s["id"].startswith(val) or s["name"] == val:
                            target_id = s["id"]
                            break
                    if not target_id:
                        raise ValueError(f"Session not found matching '{val}'")
                    if self.db.delete_session(target_id):
                        self.renderer.feed_system(f"Deleted session '{val}'.")
                        if target_id == self.session_id:
                            self.session_id = str(uuid.uuid4())
                            self.session_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            self.store.clear()
                            self.db.create_session(self.session_id, self.session_name, self.mode, self.autonomy, self.model_label, self.target)
                            self.renderer.feed_system("Active session deleted. Started a new fresh session.")
                    else:
                        raise RuntimeError(f"Failed to delete session '{val}'")
                elif sub == "current":
                    self.renderer.feed_system(f"Current Session: {self.session_name} ({self.session_id})")
                    self.renderer.feed_system(f"  Target: {self.target or 'not set'}")
                    self.renderer.feed_system(f"  Mode: {self.mode}")
                    self.renderer.feed_system(f"  Autonomy: {self.autonomy}")
                    self.renderer.feed_system(f"  Model: {self.model_label}")
                elif sub == "export":
                    export_path = Path(val or f"session_{self.session_id}.json")
                    import json
                    data = {
                        "id": self.session_id,
                        "name": self.session_name,
                        "target": self.target,
                        "mode": self.mode,
                        "autonomy": self.autonomy,
                        "messages": self.db.get_messages(self.session_id),
                        "findings": self.db.get_findings(self.session_id),
                        "tasks": self.db.get_tasks(self.session_id)
                    }
                    with open(export_path, "w") as f:
                        json.dump(data, f, indent=2)
                    self.renderer.feed_system(f"Session successfully exported to {export_path.resolve()}")
                else:
                    raise ValueError(f"Unknown session subcommand: {sub}")
            elif cmd == "mode":
                if not arg:
                    self.push_screen(
                        OptionSelectionScreen(
                            title="Mode Selection",
                            current_value=self.mode,
                            options=[(mode, mode) for mode in MODES],
                            help_text="Choose the active RedForge operating mode.",
                        ),
                        self._handle_mode_selection,
                    )
                elif arg in MODES:
                    self.mode = arg
                    self.renderer.feed_system(f"Mode set to {arg}")
                else:
                    raise ValueError(f"Unknown mode: {arg or '<missing>'}")
            elif cmd == "model":
                if not arg:
                    from redforge.core.config import get_settings

                    settings = get_settings()
                    self.push_screen(
                        ModelSelectionScreen(
                            current_provider=settings.llm.provider,
                            current_model=settings.llm.model,
                            current_api_key=settings.llm.api_key if settings.llm.provider != "ollama" else "",
                            list_models_cb=self._list_models_for_provider,
                        ),
                        self._handle_model_selection,
                    )
                else:
                    try:
                        from redforge.llm.base import ProviderFactory

                        provider, model = self._parse_model_arg(arg)
                        if provider not in ProviderFactory.list_providers():
                            raise ValueError(f"unknown provider '{provider}'")
                        if not model:
                            raise ValueError("missing model name")
                        settings_api_key = ""
                        if provider != "ollama":
                            from redforge.core.config import get_settings
                            settings_api_key = get_settings().llm.api_key
                            if not settings_api_key:
                                raise ValueError("API key required for hosted providers; use /model to open selector")
                        self._persist_llm_settings(provider, model, settings_api_key)
                        self._rebuild_agent(provider, model)
                    except Exception as exc:
                        raise RuntimeError(f"Model switch failed: {exc}")
            elif cmd == "files":
                self._refresh_project_files()
                if self._project_files:
                    self.renderer.feed_system(f"Project root: {self._project_root}")
                    for path in self._project_files[:12]:
                        self.renderer.feed_system(self._format_relpath(path))
                else:
                    self.renderer.feed_system(f"No files found under {self._project_root}")
            elif cmd == "cwd":
                next_root = self._resolve_project_path(arg or ".")
                if not next_root.exists() or not next_root.is_dir():
                    raise ValueError(f"Invalid directory: {next_root}")
                else:
                    self._project_root = next_root
                    self._attached_files = [path for path in self._attached_files if path.exists()]
                    self._refresh_project_files()
                    self.renderer.feed_system(f"Project root set to {self._project_root}")
            elif cmd == "file":
                if not arg:
                    raise ValueError("Usage: /file <path>")
                else:
                    path = self._resolve_project_path(arg)
                    if not path.exists() or not path.is_file():
                        raise ValueError(f"File not found: {path}")
                    else:
                        if path not in self._attached_files:
                            self._attached_files.append(path)
                        self.renderer.feed_system(f"Attached {self._format_relpath(path)}")
                        self.renderer.feed_tool_result(
                            "file",
                            f"attach {self._format_relpath(path)}",
                            self._read_file_context(path, limit=1200),
                            status="done",
                        )
            elif cmd == "unfile":
                if not arg:
                    raise ValueError("Usage: /unfile <path>")
                else:
                    path = self._resolve_project_path(arg)
                    self._attached_files = [item for item in self._attached_files if item != path]
                    self.renderer.feed_system(f"Detached {self._format_relpath(path)}")
            elif cmd == "target":
                self.target = arg
                self.renderer.feed_system(f"Target set to {arg or 'cleared'}")
            elif cmd == "autonomy":
                if not arg:
                    self.push_screen(
                        OptionSelectionScreen(
                            title="Autonomy Selection",
                            current_value=self.autonomy,
                            options=[(level, level) for level in ("manual", "partial", "full")],
                            help_text="Choose how much the agent can act without confirmation.",
                        ),
                        self._handle_autonomy_selection,
                    )
                elif arg in {"manual", "partial", "full"}:
                    self.autonomy = arg
                    self.renderer.feed_system(f"Autonomy set to {arg}")
                else:
                    raise ValueError(f"Unknown autonomy level: {arg or '<missing>'}")
            elif cmd == "status":
                self.renderer.feed_system(
                    f"mode={self.mode} autonomy={self.autonomy} "
                    f"target={self.target or 'unset'} model={self.model_label}"
                )
            elif cmd == "findings":
                findings = [m for m in self.store._msgs if m.role == "finding"]
                if findings:
                    self.renderer.feed_system(f"{len(findings)} findings in session:")
                    for finding in findings[-10:]:
                        self.renderer.feed_system(
                            f"{finding.severity or 'info'}: {finding.content}"
                        )
                else:
                    self.renderer.feed_system("No findings in this session yet.")
            elif cmd == "memory":
                from redforge.core.config import get_settings
                from redforge.memory.memory_manager import WorkspaceMemoryManager
                
                settings = get_settings()
                mm = WorkspaceMemoryManager("default", settings.memory.persist_dir, settings.memory.vector_db)
                
                subparts = arg.split(maxsplit=1)
                sub = subparts[0].lower() if subparts else ""
                val = subparts[1].strip() if len(subparts) > 1 else ""
                if not sub:
                    sub = "stats"
                
                if sub == "stats":
                    stats = mm.get_stats()
                    self.renderer.feed_system(f"Memory Stats: {stats.get('indexed_entries', 0)} entries, {stats.get('total_notes', 0)} notes, {stats.get('total_findings', 0)} findings.")
                elif sub == "clear":
                    mm.clear()
                    self.renderer.feed_system("Workspace memory cleared successfully.")
                elif sub == "rebuild":
                    self.renderer.feed_system("Rebuilding vector store index...")
                    mm.clear()
                    # Add current messages and findings
                    messages = self.db.get_messages(self.session_id)
                    findings = self.db.get_findings(self.session_id)
                    for m in messages:
                        mm.add_session(m["role"], m["content"], {"timestamp": m.get("timestamp")})
                    for f in findings:
                        mm.add_finding(f["type"], f["title"], f["description"], f["severity"], f["target"], f.get("evidence"))
                    self.renderer.feed_system("Vector store index rebuilt successfully.")
                elif sub == "search":
                    if not val:
                        raise ValueError("Usage: /memory search <query>")
                    results = mm.search(val, limit=5)
                    if not results:
                        self.renderer.feed_system(f"No memory results found for '{val}'.")
                    else:
                        self.renderer.feed_system(f"Memory search results for '{val}':")
                        for idx, res in enumerate(results, 1):
                            self.renderer.feed_system(f"{idx}. [score: {res.score:.2f}] {res.content}")
                else:
                    raise ValueError(f"Unknown memory subcommand: {sub}")
            else:
                raise ValueError(f"Unknown command: {raw}")
            logger.info("Command Executed: %s", clean_raw)
        except Exception as exc:
            logger.exception("Command Failed: %s. Reason: %s", raw, exc)
            
            suggested_fix = "Verify the command syntax or use /help."
            if cmd == "mode":
                suggested_fix = "Use one of the supported modes: bugbounty, ctf, learning, android, coding."
            elif cmd == "autonomy":
                suggested_fix = "Use one of the supported autonomy levels: manual, partial, full."
            elif cmd == "model":
                suggested_fix = "Open the selector using /model without arguments, or specify provider:model."
            elif cmd == "file" or cmd == "unfile":
                suggested_fix = "Verify that the path points to a valid file."
            
            error_msg = f"Command Failed\nReason: {exc}\nSuggested Fix: {suggested_fix}"
            self.renderer.feed_error(error_msg)

        self._refresh_transcript()

    async def _shell(self, command: str) -> None:
        if not command:
            self.renderer.feed_error("Missing shell command after !")
            self._refresh_transcript()
            return

        self.renderer.feed_user(f"! {command}")
        self._refresh_transcript()
        self._set_spinner(True, "running shell command…")
        osc_progress(-1)
        started = time.monotonic()

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            output = (stdout.decode(errors="replace") + stderr.decode(errors="replace")).strip()
            status = "done" if proc.returncode == 0 else "failed"
            self.renderer.feed_tool_result(
                "shell",
                command,
                output or "(no output)",
                status=status,
                duration_s=time.monotonic() - started,
            )
        except asyncio.TimeoutError:
            self.renderer.feed_tool_result(
                "shell",
                command,
                "Command timed out after 30s.",
                status="failed",
                duration_s=time.monotonic() - started,
            )
        except Exception as exc:
            self.renderer.feed_error(str(exc))
        finally:
            self.latency = (time.monotonic() - started) * 1000
            self.tokens += max(1, len(command.split()))
            self._set_spinner(False)
            osc_progress(200)
            self._refresh_transcript()

    async def _chat(self, message: str) -> None:
        self.renderer.feed_user(message)
        self._refresh_transcript()

        if self._agent_task and not self._agent_task.done():
            self._agent_task.cancel()

        self._live_agent_events = False
        self._confirmation_announced = False
        self._agent_task = asyncio.create_task(self._run_agent(self._build_message_with_file_context(message)))

    async def _run_agent(self, message: str) -> None:
        if not self._agent:
            self.renderer.feed_assistant("Agent is not configured. Add your LLM settings in config.yaml.")
            self._refresh_transcript()
            return

        from redforge.core.state import AgentMode, AutonomyLevel

        mode_map = {
            "bugbounty": AgentMode.GOAL_BASED,
            "ctf": AgentMode.GOAL_BASED,
            "android": AgentMode.GOAL_BASED,
            "learning": AgentMode.KNOWLEDGE_BASED,
            "coding": AgentMode.KNOWLEDGE_BASED,
        }
        autonomy_map = {
            "manual": AutonomyLevel.MANUAL,
            "partial": AutonomyLevel.PARTIAL,
            "full": AutonomyLevel.FULL,
        }

        self._set_spinner(True, "agent thinking…")
        osc_progress(-1)
        started = time.monotonic()

        try:
            previous_messages = len(self._prior_state.messages) if self._prior_state else 0
            state = await self._agent.run(
                user_input=message,
                workspace_id=None,
                workspace_name=None,
                autonomy_level=autonomy_map[self.autonomy],
                mode=mode_map[self.mode],
                prior_state=self._prior_state,
            )
            self._prior_state = state

            if not self._live_agent_events:
                for msg in state.messages[previous_messages:]:
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if role == "assistant":
                        self.renderer.feed_assistant(content, streaming=False)
                    elif role == "tool":
                        self.renderer.feed_tool_result("tool", "agent action", content)

            if state.total_tokens:
                self.tokens = state.total_tokens
            self.latency = (time.monotonic() - started) * 1000

            if state.pending_confirmation and not self._confirmation_announced:
                self.renderer.feed_system("Agent is waiting for approval before executing a tool action.")
        except asyncio.CancelledError:
            self.renderer.feed_system("Task cancelled.")
        except Exception as exc:
            self.renderer.feed_error(str(exc))
        finally:
            self._set_spinner(False)
            osc_progress(200)
            self._refresh_transcript()

    def action_toggle_sidebar(self) -> None:
        self._sidebar_visible = not self._sidebar_visible
        try:
            sidebar = self.query_one("#sidebar")
            sidebar.toggle_class("hidden")
        except NoMatches:
            pass

    def action_clear_output(self) -> None:
        self.store.clear()
        self._refresh_transcript()

    def action_cycle_mode(self) -> None:
        idx = (MODES.index(self.mode) + 1) % len(MODES)
        self.mode = MODES[idx]

    def action_kill_task(self) -> None:
        if self._agent_task and not self._agent_task.done():
            self._agent_task.cancel()
            self.toast_mgr.show("Cancelled active task", "warning")
        else:
            self.toast_mgr.show("No active task", "info")

    def action_focus_input(self) -> None:
        try:
            self.query_one(VimInput).focus_input()
        except NoMatches:
            pass

    def _handle_model_selection(self, result: dict | None) -> None:
        if not result:
            return
        provider = result["provider"]
        model = result["model"]
        api_key = result.get("api_key", "")
        try:
            self._persist_llm_settings(provider, model, api_key)
            self._rebuild_agent(provider, model)
            if provider != "ollama":
                self.toast_mgr.show(f"{provider} configured", "success")
            self._refresh_transcript()
        except Exception as exc:
            self.renderer.feed_error(f"Model switch failed: {exc}")
            self._refresh_transcript()

    def _handle_mode_selection(self, result: str | None) -> None:
        if not result:
            return
        self.mode = result
        self.renderer.feed_system(f"Mode set to {result}")
        self._refresh_transcript()

    def _handle_autonomy_selection(self, result: str | None) -> None:
        if not result:
            return
        self.autonomy = result
        self.renderer.feed_system(f"Autonomy set to {result}")
        self._refresh_transcript()

    def _handle_file_mention(self, result: str | None) -> None:
        if not result:
            return
        try:
            vim = self.query_one(VimInput)
            vim.replace_active_mention(result)
            vim.focus_input()
        except NoMatches:
            pass


def launch() -> None:
    RedForgeTUI().run()


def launch_tui() -> None:
    launch()


if __name__ == "__main__":
    launch()

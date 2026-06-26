"""
RedForge TUI — Palette & Notifications
CommandPalette for fuzzy command execution.
Toast/ToastManager for non-blocking alerts.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Input, Select, Static, OptionList
from textual.widgets.option_list import Option

from rich.markup import escape
from rich.text import Text

from pathlib import Path
from redforge.tui.renderer import ACCENT, BG, BG_PANEL, BORDER, FG, FG_DIM, FG_MUTED, SEV_COLOR, _e


# ─── CommandRegistry ──────────────────────────────────────

class CommandRegistry:
    """Registry for built-in and dynamic slash commands in RedForge."""
    
    _builtins: Dict[str, str] = {
        "/help": "Show all available commands",
        "/clear": "Clear conversation output",
        "/mode": "Change active mode (bugbounty/ctf/...)",
        "/model": "Open provider/model selection",
        "/target": "Set scan target",
        "/autonomy": "Set autonomy (manual/partial/full)",
        "/status": "Show agent status",
        "/findings": "List all findings",
        "/files": "List files in the active root",
        "/file": "Attach a CTF file for analysis",
        "/unfile": "Detach an attached CTF file",
        "/cwd": "Change the CTF file root directory",
        "/session": "Manage sessions (list, load, save, delete, current, export)",
        "/report": "Generate and manage reports (generate, export, list)",
        "/tools": "Manage tools (list, verify, install, update)",
        "/memory": "Manage memory (stats, search, clear, rebuild)",
        "/history": "Display previous interactions with filtering",
        "/workspace": "Manage workspace (info, files, reset)",
        "/doctor": "Check system health and dependencies",
        "/config": "View or update settings",
        "/exit": "Exit the application",
        "/approved": "Execute the planned action"
    }
    
    _nested_commands: Dict[str, List[Dict[str, str]]] = {
        "/session": [
            {"cmd": "list", "desc": "List all sessions"},
            {"cmd": "load", "desc": "Load a session by ID"},
            {"cmd": "save", "desc": "Save current session"},
            {"cmd": "delete", "desc": "Delete a session"},
            {"cmd": "current", "desc": "Show current session info"},
            {"cmd": "export", "desc": "Export session data"},
        ],
        "/tools": [
            {"cmd": "list", "desc": "List all tools"},
            {"cmd": "install", "desc": "Install a tool"},
            {"cmd": "update", "desc": "Update tools"},
            {"cmd": "verify", "desc": "Verify tool installations"},
        ],
        "/memory": [
            {"cmd": "stats", "desc": "Show memory statistics"},
            {"cmd": "clear", "desc": "Clear workspace memory"},
            {"cmd": "search", "desc": "Search memory"},
            {"cmd": "rebuild", "desc": "Rebuild memory index"},
        ],
        "/report": [
            {"cmd": "generate", "desc": "Generate a findings report"},
            {"cmd": "export", "desc": "Export report to specific path"},
            {"cmd": "list", "desc": "List generated reports"},
        ],
        "/workspace": [
            {"cmd": "info", "desc": "Show workspace details"},
            {"cmd": "files", "desc": "List workspace files"},
            {"cmd": "reset", "desc": "Reset workspace state"},
        ]
    }
    
    _dynamic_commands: Dict[str, str] = {}

    @staticmethod
    def _normalize(name: str) -> str:
        if not isinstance(name, str):
            return ""
        normalized = " ".join(name.strip().split())
        if not normalized:
            return ""
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        return normalized

    @classmethod
    def register(cls, name: str, desc: str) -> None:
        """Register a command dynamically."""
        name = cls._normalize(name)
        if not name or name == "/" or any(char.isspace() for char in name[1:]):
            raise ValueError("Command names must be a single slash-prefixed token")
        if not isinstance(desc, str) or not desc.strip():
            raise ValueError("Command descriptions must be non-empty strings")
        cls._dynamic_commands[name] = desc.strip()
        logger.info("Command Registered: %s", name)

    @classmethod
    def get_nested_commands(cls, prefix: str) -> List[Dict[str, str]]:
        """Retrieve nested commands for a given prefix command."""
        return list(cls._nested_commands.get(cls._normalize(prefix), ()))

    @classmethod
    def get_commands(cls) -> List[Dict[str, str]]:
        """Retrieve all commands from builtins and dynamic commands."""
        merged = {**cls._builtins, **cls._dynamic_commands}
        return [
            {"cmd": name, "desc": desc}
            for name, desc in merged.items()
            if cls._is_valid_entry(name, desc)
        ]

    @classmethod
    def _is_valid_entry(cls, name: object, desc: object) -> bool:
        return (
            isinstance(name, str)
            and cls._normalize(name) == name
            and name != "/"
            and not any(char.isspace() for char in name[1:])
            and isinstance(desc, str)
            and bool(desc.strip())
        )

    @classmethod
    def exists(cls, name: str) -> bool:
        """Check if a command is valid in the registry (supports nested commands)."""
        name = cls._normalize(name)
        if not name:
            return False
        parts = name.split()
        base = parts[0]
        if base not in {c["cmd"] for c in cls.get_commands()}:
            return False

        if len(parts) > 1 and base in cls._nested_commands:
            sub = parts[1]
            nested_list = [
                nested.get("cmd")
                for nested in cls._nested_commands[base]
                if isinstance(nested, dict)
            ]
            return sub in nested_list

        return True


# ─── CommandPalette ──────────────────────────────────────

class CommandPalette(Widget):
    """
    Fuzzy search launcher for slash commands.
    Triggered by Tab when input starts with `/`.
    """

    DEFAULT_CSS = f"""
    CommandPalette {{
        layer: overlay;
        align: center middle;
        width: 100%;
        height: 100%;
        background: #00000088;
    }}
    #cp-box {{
        width: 70;
        height: 16;
        background: {BG_PANEL};
        border: thick {ACCENT};
        layout: vertical;
    }}
    #cp-input {{
        border: none;
        border-bottom: tall {FG_DIM};
        background: {BG_PANEL};
        color: {FG};
        padding: 1 2;
    }}
    #cp-option-list {{
        height: 1fr;
        background: {BG_PANEL};
        color: {FG_MUTED};
        border: none;
    }}
    #cp-option-list > .option-list--option {{
        padding: 0 2;
    }}
    #cp-option-list > .option-list--option-highlighted {{
        background: {FG_DIM} !important;
        color: {FG} !important;
        text-style: bold;
    }}
    #cp-option-list:focus > .option-list--option-highlighted {{
        background: {FG_DIM} !important;
        color: {FG} !important;
        text-style: bold;
    }}
    #cp-option-list > .option-list--option-hover {{
        background: {BORDER} !important;
    }}
    """

    def __init__(self, initial_query: str = "") -> None:
        super().__init__()
        self.initial_query = initial_query
        self.on_select: Callable[[str], None] | None = None
        self._matches: List[Dict[str, str]] = []
        self._idx = 0
        self._selection_committed = False

    def _get_base_commands(self) -> List[Dict[str, str]]:
        return CommandRegistry.get_commands()

    def _valid_commands(self) -> List[Dict[str, str]]:
        commands: List[Dict[str, str]] = []
        seen: set[str] = set()
        for command in self._get_base_commands():
            try:
                name = command["cmd"]
                desc = command["desc"]
                if (
                    name not in seen
                    and CommandRegistry.exists(name)
                    and isinstance(desc, str)
                    and desc.strip()
                ):
                    commands.append({"cmd": name, "desc": desc.strip()})
                    seen.add(name)
            except (KeyError, TypeError, AttributeError, IndexError):
                logger.warning("Ignoring invalid command registry entry: %r", command)
        return commands

    def compose(self) -> ComposeResult:
        with Vertical(id="cp-box"):
            yield Input(placeholder="Search commands...", id="cp-input", value=self.initial_query)
            yield OptionList(id="cp-option-list")

    def on_mount(self) -> None:
        self._filter(self.initial_query)
        inp = self.query_one("#cp-input", Input)
        inp.focus()
        inp.cursor_position = len(inp.value)

    @on(Input.Changed, "#cp-input")
    def _on_input(self, event: Input.Changed) -> None:
        self._filter(event.value)

    def _filter(self, query: str) -> None:
        q = query.strip()
        valid_commands = self._valid_commands()

        def fuzzy_score(needle: str, target: str) -> Optional[tuple[int, int, int]]:
            needle = needle.lower().lstrip("/")
            target = target.lower().lstrip("/")
            if not needle:
                return (0, 0, len(target))
            i = 0
            positions: List[int] = []
            for char in needle:
                found = target.find(char, i)
                if found == -1:
                    return None
                positions.append(found)
                i = found + 1
            gaps = sum(b - a - 1 for a, b in zip(positions, positions[1:]))
            return (positions[0], gaps, len(target))
        
        trigger_nested = False
        prefix = ""
        subquery = ""
        for p in CommandRegistry._nested_commands:
            if query.startswith(p + " "):
                trigger_nested = True
                prefix = p
                subquery = query[len(p) + 1:].strip()
                break

        if trigger_nested:
            nested = CommandRegistry.get_nested_commands(prefix)
            valid_nested = []
            for n in nested:
                try:
                    full_cmd = f"{prefix} {n['cmd']}"
                    if (
                        CommandRegistry.exists(full_cmd)
                        and isinstance(n["desc"], str)
                        and n["desc"].strip()
                    ):
                        valid_nested.append(n)
                except (KeyError, TypeError, AttributeError, IndexError):
                    logger.warning("Ignoring invalid nested command entry: %r", n)
            
            if not subquery:
                self._matches = [{"cmd": f"{prefix} {n['cmd']}", "desc": n["desc"]} for n in valid_nested]
            else:
                scored = []
                for nested_command in valid_nested:
                    score = fuzzy_score(subquery, nested_command["cmd"])
                    desc_score = fuzzy_score(subquery, nested_command["desc"])
                    best_score = min(
                        (candidate for candidate in (score, desc_score) if candidate is not None),
                        default=None,
                    )
                    if best_score is not None:
                        scored.append((best_score, nested_command))
                scored.sort(key=lambda item: item[0])
                self._matches = [
                    {"cmd": f"{prefix} {item['cmd']}", "desc": item["desc"]}
                    for _, item in scored
                ]
        else:
            if not q:
                self._matches = valid_commands
            else:
                scored = []
                for command in valid_commands:
                    command_score = fuzzy_score(q, command["cmd"])
                    desc_score = fuzzy_score(q, command["desc"])
                    best_score = min(
                        (
                            candidate
                            for candidate in (command_score, desc_score)
                            if candidate is not None
                        ),
                        default=None,
                    )
                    if best_score is not None:
                        scored.append((best_score, command))
                scored.sort(key=lambda item: item[0])
                self._matches = [command for _, command in scored]
                
        self._idx = 0
        self._render_list()

    def _render_list(self) -> None:
        try:
            ol = self.query_one("#cp-option-list", OptionList)
            ol.clear_options()
            
            options = []
            for match in self._matches:
                prompt = Text.from_markup(f"[bold {ACCENT}]{match['cmd']:<12}[/] {escape(match['desc'])}")
                options.append(Option(prompt, id=match['cmd']))
                
            ol.add_options(options)
            if self._matches:
                ol.highlighted = self._idx
        except (NoMatches, KeyError, TypeError, IndexError) as exc:
            logger.error("Command palette render failed: %s", exc)

    @on(OptionList.OptionSelected, "#cp-option-list")
    def _on_option_selected(self, event: OptionList.OptionSelected) -> None:
        self._confirm(event.option_id)

    @on(OptionList.OptionHighlighted, "#cp-option-list")
    def _on_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_index is not None and 0 <= event.option_index < len(self._matches):
            self._idx = event.option_index

    def _confirm(self, command: Optional[str] = None) -> None:
        if self._selection_committed:
            return
        if command is None and self._matches and 0 <= self._idx < len(self._matches):
            command = self._matches[self._idx]["cmd"]
        if not command or not CommandRegistry.exists(command):
            return

        self._selection_committed = True
        logger.info("Command Selected: %s", command)
        try:
            if self.on_select:
                self.on_select(command)
        except Exception as exc:
            logger.exception("Command Failed: %s. Reason: %s", command, exc)
            try:
                self.app.notify(
                    f"Command Failed\nReason: {exc}\nSuggested Fix: Retry or use /help.",
                    severity="error",
                )
            except Exception:
                pass
        finally:
            self.remove()

    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.remove()
            event.prevent_default()
            event.stop()
        elif event.key in ("down", "tab"):
            ol = self.query_one("#cp-option-list", OptionList)
            if self._matches:
                self._idx = (self._idx + 1) % len(self._matches)
                ol.highlighted = self._idx
                ol.scroll_to_highlight()
            event.prevent_default()
            event.stop()
        elif event.key in ("up", "shift+tab"):
            ol = self.query_one("#cp-option-list", OptionList)
            if self._matches:
                self._idx = (self._idx - 1) % len(self._matches)
                ol.highlighted = self._idx
                ol.scroll_to_highlight()
            event.prevent_default()
            event.stop()
        elif event.key == "enter":
            self._confirm()
            event.prevent_default()
            event.stop()


# ─── Toast Notifications ─────────────────────────────────

class Toast(Widget):
    """A transient notification."""

    DEFAULT_CSS = f"""
    Toast {{
        width: 40;
        height: auto;
        background: {BG_PANEL};
        border: solid {FG_DIM};
        padding: 0 1;
        margin: 0 0 1 0;
    }}
    """

    message: str = ""
    level: str = "info"  # info, success, warning, error

    def render(self) -> str:
        color = {
            "info": FG_MUTED,
            "success": "#00cc66",
            "warning": "#ffcc00",
            "error": "#ff3333",
        }.get(self.level, FG)
        icon = {
            "info": "ℹ",
            "success": "✓",
            "warning": "⚠",
            "error": "✗",
        }.get(self.level, "●")

        return f"[bold {color}]{icon}[/] {_e(self.message)}"

    def on_mount(self) -> None:
        color = {
            "info": FG_DIM, "success": "#00cc66",
            "warning": "#ffcc00", "error": "#ff3333"
        }.get(self.level, FG_DIM)
        self.styles.border = ("solid", color)


class ToastManager(Widget):
    """
    Manages a stack of Toast notifications in the top-right corner.
    """

    DEFAULT_CSS = """
    ToastManager {
        layer: toast;
        align: right top;
        width: 44;
        height: auto;
        margin: 1 2 0 0;
        layout: vertical;
    }
    """

    def show(self, message: str, level: str = "info", duration: float = 3.0) -> None:
        toast = Toast()
        toast.message = message
        toast.level = level
        self.mount(toast)

        # Auto-remove
        def remove_toast():
            try:
                toast.remove()
            except Exception:
                pass

        self.set_timer(duration, remove_toast)


class ModelSelectionScreen(ModalScreen[dict | None]):
    """Modal for selecting provider, model, and API key."""

    DEFAULT_CSS = f"""
    ModelSelectionScreen {{
        align: center middle;
        background: #000000aa;
    }}
    #model-modal {{
        width: 84;
        height: auto;
        padding: 1 2;
        background: {BG_PANEL};
        border: tall {FG_DIM};
        layout: vertical;
    }}
    #model-title {{
        color: {FG};
        text-style: bold;
        padding-bottom: 1;
    }}
    .model-label {{
        color: {FG_MUTED};
        padding-top: 1;
    }}
    .model-help {{
        color: {FG_DIM};
        padding-top: 1;
    }}
    #model-actions {{
        height: auto;
        padding-top: 1;
    }}
    #api-wrap.hidden {{
        display: none;
    }}
    """

    def __init__(
        self,
        *,
        current_provider: str,
        current_model: str,
        current_api_key: str,
        list_models_cb: Callable[
            [str, str],
            Awaitable[List[str]],
        ],
    ) -> None:
        super().__init__()
        self.current_provider = current_provider
        self.current_model = current_model
        self.current_api_key = current_api_key
        self.list_models_cb = list_models_cb

    def compose(self) -> ComposeResult:
        provider_options = [
            (provider, provider) for provider in ("ollama", "openai", "anthropic", "gemini", "groq")
        ]
        with Vertical(id="model-modal"):
            yield Static("Model Selection", id="model-title")
            yield Static("Provider", classes="model-label")
            yield Select(provider_options, value=self.current_provider, id="provider-select", allow_blank=False)
            yield Static("Available Models", classes="model-label")
            yield Select([("Loading…", "__loading__")], value="__loading__", id="model-select", allow_blank=False)
            yield Static("Model Name", classes="model-label")
            yield Input(value=self.current_model, placeholder="Enter model name", id="model-input")
            with Vertical(id="api-wrap"):
                yield Static("API Key", classes="model-label")
                yield Input(value=self.current_api_key, password=True, placeholder="Required for hosted providers", id="api-input")
            yield Static("Use arrows in selects, or type a model manually. Enter applies.", classes="model-help")
            with Horizontal(id="model-actions"):
                yield Button("Apply", id="apply-model", variant="primary")
                yield Button("Cancel", id="cancel-model")

    async def on_mount(self) -> None:
        await self._load_models_for_provider(self.current_provider)
        self._toggle_api_visibility(self.current_provider)

    @on(Select.Changed, "#provider-select")
    async def _provider_changed(self, event: Select.Changed) -> None:
        provider = str(event.value)
        self._toggle_api_visibility(provider)
        if provider != "ollama":
            self.query_one("#api-input", Input).focus()
        await self._load_models_for_provider(provider)

    @on(Select.Changed, "#model-select")
    def _model_changed(self, event: Select.Changed) -> None:
        value = str(event.value)
        if value and value not in {"__loading__", "__manual__"}:
            self.query_one("#model-input", Input).value = value

    @on(Button.Pressed, "#cancel-model")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#apply-model")
    def _apply_button(self) -> None:
        self._apply()

    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "enter":
            focused = self.focused
            if isinstance(focused, Input):
                self._apply()

    async def _load_models_for_provider(self, provider: str) -> None:
        model_select = self.query_one("#model-select", Select)
        model_select.set_options([("Loading…", "__loading__")])
        model_select.value = "__loading__"
        try:
            api_key = self.query_one("#api-input", Input).value if provider != "ollama" else ""
        except NoMatches:
            api_key = ""
        models = await self.list_models_cb(provider, api_key)
        options = [(model, model) for model in models] if models else [("Manual entry", "__manual__")]
        model_select.set_options(options)

        target_model = self.query_one("#model-input", Input).value.strip() or self.current_model
        available_values = [value for _, value in options]
        model_select.value = target_model if target_model in available_values else available_values[0]

    def _toggle_api_visibility(self, provider: str) -> None:
        wrap = self.query_one("#api-wrap")
        if provider == "ollama":
            wrap.add_class("hidden")
        else:
            wrap.remove_class("hidden")

    def _apply(self) -> None:
        provider = str(self.query_one("#provider-select", Select).value)
        model = self.query_one("#model-input", Input).value.strip()
        api_key = self.query_one("#api-input", Input).value.strip()
        if not model:
            self.app.notify("Model name is required", severity="warning")
            return
        if provider != "ollama" and not api_key:
            self.app.notify("API key is required for hosted providers", severity="warning")
            return
        self.dismiss({"provider": provider, "model": model, "api_key": api_key})


class OptionSelectionScreen(ModalScreen[str | None]):
    """Simple modal for mode/autonomy selection."""

    DEFAULT_CSS = f"""
    OptionSelectionScreen {{
        align: center middle;
        background: #000000aa;
    }}
    #option-modal {{
        width: 56;
        height: auto;
        padding: 1 2;
        background: {BG_PANEL};
        border: tall {FG_DIM};
        layout: vertical;
    }}
    #option-title {{
        color: {FG};
        text-style: bold;
        padding-bottom: 1;
    }}
    #option-help {{
        color: {FG_DIM};
        padding-top: 1;
    }}
    #option-actions {{
        height: auto;
        padding-top: 1;
    }}
    """

    def __init__(self, *, title: str, current_value: str, options: list[tuple[str, str]], help_text: str) -> None:
        super().__init__()
        self._option_title = title
        self.current_value = current_value
        self.options = options
        self.help_text = help_text

    def compose(self) -> ComposeResult:
        with Vertical(id="option-modal"):
            yield Static(self._option_title, id="option-title")
            yield Select(self.options, value=self.current_value, id="option-select", allow_blank=False)
            yield Static(self.help_text, id="option-help")
            with Horizontal(id="option-actions"):
                yield Button("Apply", id="apply-option", variant="primary")
                yield Button("Cancel", id="cancel-option")

    @on(Button.Pressed, "#cancel-option")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#apply-option")
    def _apply_button(self) -> None:
        self.dismiss(str(self.query_one("#option-select", Select).value))

    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "enter":
            self.dismiss(str(self.query_one("#option-select", Select).value))


class ConfirmationModal(ModalScreen[bool]):
    """Modal for confirming a tool action."""

    DEFAULT_CSS = f"""
    ConfirmationModal {{
        align: center middle;
        background: #000000aa;
    }}
    #confirm-modal {{
        width: 64;
        height: auto;
        padding: 1 2;
        background: {BG_PANEL};
        border: thick {ACCENT};
        layout: vertical;
    }}
    #confirm-title {{
        color: {ACCENT};
        text-style: bold;
        padding-bottom: 1;
    }}
    #confirm-message {{
        color: {FG};
        padding-bottom: 1;
    }}
    #confirm-command {{
        background: {BG};
        color: #ffcc00;
        padding: 1 1;
        margin-bottom: 1;
        border: solid {FG_DIM};
    }}
    #confirm-actions {{
        height: auto;
        padding-top: 1;
    }}
    """

    def __init__(self, message: str, command: str = "") -> None:
        super().__init__()
        self._message = message
        self._command = command

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-modal"):
            yield Static("Manual Approval Required", id="confirm-title")
            yield Static(self._message, id="confirm-message")
            if self._command:
                yield Static(f"$ {self._command}", id="confirm-command")
            with Horizontal(id="confirm-actions"):
                yield Button("Approve", id="approve-btn", variant="primary")
                yield Button("Reject", id="reject-btn")

    @on(Button.Pressed, "#approve-btn")
    def _approve(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#reject-btn")
    def _reject(self) -> None:
        self.dismiss(False)

    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(False)
        elif event.key == "enter":
            self.dismiss(True)


class FileMentionScreen(ModalScreen[str | None]):
    """Modal for selecting a workspace file to insert as an @mention."""

    DEFAULT_CSS = f"""
    FileMentionScreen {{
        align: center middle;
        background: #000000aa;
    }}
    #file-modal {{
        width: 88;
        height: 24;
        background: {BG_PANEL};
        border: tall {FG_DIM};
        layout: vertical;
        padding: 1 1;
    }}
    #file-title {{
        color: {FG};
        text-style: bold;
        padding: 0 1 1 1;
    }}
    #file-search {{
        border: none;
        border-bottom: solid {FG_DIM};
        background: {BG_PANEL};
        color: {FG};
        padding: 0 1;
    }}
    #file-list {{
        height: 1fr;
        padding: 1 0;
        overflow-y: auto;
    }}
    .file-item {{
        color: {FG_MUTED};
        padding: 0 1;
    }}
    .file-item-active {{
        color: {FG};
        background: {FG_DIM};
        text-style: bold;
        padding: 0 1;
    }}
    #file-help {{
        color: {FG_DIM};
        padding: 0 1;
    }}
    """

    def __init__(self, *, files: List[str], query: str = "") -> None:
        super().__init__()
        self._files = files
        self._query = query
        self._matches: List[str] = []
        self._idx = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="file-modal"):
            yield Static("Insert File Mention", id="file-title")
            yield Input(value=self._query, placeholder="Search files or directories…", id="file-search")
            yield Vertical(id="file-list")
            yield Static("Enter inserts `@path`. Escape closes.", id="file-help")

    def on_mount(self) -> None:
        self._filter(self._query)
        self.query_one("#file-search", Input).focus()

    @on(Input.Changed, "#file-search")
    def _search_changed(self, event: Input.Changed) -> None:
        self._filter(event.value)

    def _filter(self, query: str) -> None:
        q = query.lower().strip()
        if not q:
            self._matches = self._files[:]
        else:
            matches = []
            for path in self._files:
                path_lower = path.lower()
                i = 0
                for char in q:
                    i = path_lower.find(char, i)
                    if i == -1:
                        break
                    i += 1
                else:
                    matches.append(path)
            self._matches = matches
        self._idx = 0
        logger.debug(f"Suggestions Generated: {len(self._matches)} matches for query '{query}'")
        self._render_list()

    def _render_list(self) -> None:
        try:
            lst = self.query_one("#file-list", Vertical)
            lst.remove_children()
            if not self._matches:
                lst.mount(Static("No matching files", classes="file-item"))
                return
            for i, match in enumerate(self._matches[:100]):
                classes = "file-item-active" if i == self._idx else "file-item"
                lst.mount(Static(match, classes=classes))
        except NoMatches:
            pass

    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "down":
            if self._matches:
                self._idx = (self._idx + 1) % len(self._matches[:100])
                self._render_list()
            event.prevent_default()
        elif event.key == "up":
            if self._matches:
                self._idx = (self._idx - 1) % len(self._matches[:100])
                self._render_list()
            event.prevent_default()
        elif event.key == "enter":
            if self._matches:
                selection = f"@{self._matches[self._idx]}"
                logger.debug(f"Mention Selected: {selection}")
                self.dismiss(selection)
            else:
                self.dismiss(None)


# ─── New Modal Screens ───────────────────────────────────

class SaveSessionScreen(ModalScreen[str | None]):
    """Modal for entering a session name to save."""
    DEFAULT_CSS = f"""
    SaveSessionScreen {{
        align: center middle;
        background: #000000aa;
    }}
    #save-session-modal {{
        width: 50;
        height: auto;
        padding: 1 2;
        background: {BG_PANEL};
        border: tall {FG_DIM};
        layout: vertical;
    }}
    #save-title {{
        color: {FG};
        text-style: bold;
        padding-bottom: 1;
    }}
    #save-actions {{
        height: auto;
        padding-top: 1;
    }}
    """
    def __init__(self, current_name: str) -> None:
        super().__init__()
        self.current_name = current_name

    def compose(self) -> ComposeResult:
        with Vertical(id="save-session-modal"):
            yield Static("Save Session", id="save-title")
            yield Input(value=self.current_name, placeholder="Enter session name", id="save-input")
            with Horizontal(id="save-actions"):
                yield Button("Save", id="confirm-save", variant="primary")
                yield Button("Cancel", id="cancel-save")

    @on(Button.Pressed, "#cancel-save")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#confirm-save")
    def _save(self) -> None:
        name = self.query_one("#save-input", Input).value.strip()
        self.dismiss(name if name else None)

    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "enter":
            name = self.query_one("#save-input", Input).value.strip()
            self.dismiss(name if name else None)


class FindingsScreen(ModalScreen[None]):
    """Modal for viewing all session security findings."""
    DEFAULT_CSS = f"""
    FindingsScreen {{
        align: center middle;
        background: #000000aa;
    }}
    #findings-modal {{
        width: 90;
        height: 28;
        padding: 1 2;
        background: {BG_PANEL};
        border: tall {FG_DIM};
        layout: vertical;
    }}
    #findings-title {{
        color: {FG};
        text-style: bold;
        padding-bottom: 1;
    }}
    #findings-list {{
        height: 1fr;
        overflow-y: auto;
        border: solid {FG_DIM};
        padding: 1 1;
    }}
    #findings-actions {{
        height: auto;
        padding-top: 1;
    }}
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="findings-modal"):
            yield Static("Session Findings", id="findings-title")
            yield OptionList(id="findings-list")
            with Horizontal(id="findings-actions"):
                yield Button("Close", id="close-findings")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        ol = self.query_one("#findings-list", OptionList)
        ol.clear_options()
        findings = self.app.db.get_findings(self.app.session_id)
        if not findings:
            ol.add_option(Option("No findings recorded in this session yet.", disabled=True))
            return
        
        for idx, f in enumerate(findings, 1):
            severity = f.get("severity", "medium").upper()
            sev_color = SEV_COLOR.get(f.get("severity", "medium").lower(), "#ffffff")
            title = f.get("title", "Finding")
            desc = f.get("description", "")
            prompt = f"[{sev_color}][{severity}][/{sev_color}] {idx}. {title} - {desc}"
            ol.add_option(Option(prompt))

    @on(Button.Pressed, "#close-findings")
    def _close(self) -> None:
        self.dismiss()

    async def on_key(self, event: events.Key) -> None:
        if event.key in ("escape", "enter"):
            self.dismiss()


class ReportScreen(ModalScreen[None]):
    """Modal for generating, viewing, and exporting reports."""
    DEFAULT_CSS = f"""
    ReportScreen {{
        align: center middle;
        background: #000000aa;
    }}
    #report-modal {{
        width: 88;
        height: 26;
        padding: 1 2;
        background: {BG_PANEL};
        border: tall {FG_DIM};
        layout: vertical;
    }}
    #report-title {{
        color: {FG};
        text-style: bold;
        padding-bottom: 1;
    }}
    #report-options {{
        height: auto;
        layout: horizontal;
        padding-bottom: 1;
    }}
    #report-list {{
        height: 1fr;
        border: solid {FG_DIM};
        background: {BG};
        overflow-y: auto;
        padding: 0 1;
    }}
    #report-actions {{
        height: auto;
        padding-top: 1;
    }}
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="report-modal"):
            yield Static("Security Assessment Reports", id="report-title")
            with Horizontal(id="report-options"):
                yield Button("Generate Report", id="generate-report-btn", variant="primary")
                yield Button("Export to Markdown", id="export-report-btn")
            yield Static("Generated Report Files under workspaces/default/reports/:", classes="model-label")
            yield OptionList(id="report-list")
            with Horizontal(id="report-actions"):
                yield Button("Close", id="close-reports")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        ol = self.query_one("#report-list", OptionList)
        ol.clear_options()
        
        report_dir = Path("workspaces") / "default" / "reports"
        if report_dir.exists():
            reports = list(report_dir.glob("*.md"))
            if reports:
                for r in reports:
                    ol.add_option(Option(f"📄 {r.name} ({r.stat().st_size} bytes)"))
            else:
                ol.add_option(Option("No report files found.", disabled=True))
        else:
            ol.add_option(Option("No reports directory exists yet.", disabled=True))

    @on(Button.Pressed, "#generate-report-btn")
    def _generate(self) -> None:
        findings = [m for m in self.app.store._msgs if m.role == "finding"]
        if not findings:
            self.app.toast_mgr.show("No findings in this session to report.", "warning")
            return
        
        from redforge.advanced import ReportGenerator
        from datetime import datetime
        rg = ReportGenerator()
        report_findings = [{"title": "Vulnerability Finding", "severity": f.severity or "INFO", "cvss_score": 0.0, "cwe_id": "N/A", "description": f.content, "impact": "Potential security compromise.", "remediation": "Review codebase and apply appropriate fix."} for f in findings]
        report_data = {
            "title": f"Security Assessment Report for {self.app.target or 'Unknown Target'}",
            "target": self.app.target or "localhost",
            "author": "RedForge TUI",
            "scope": [self.app.target] if self.app.target else ["In-scope codebase"],
            "findings": report_findings,
            "summary": f"A total of {len(findings)} findings were identified during the assessment.",
            "methodology": "Automated security review and analysis.",
            "limitations": "Standard constraints of automated scanning."
        }
        rg.create_report(report_data, session_target=self.app.target)
        report_dir = Path("workspaces") / "default" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        rg.save_report(report_path, format="md")
        self.app.toast_mgr.show(f"Report generated: {report_path.name}", "success")
        self.app.renderer.feed_system(f"Report successfully generated and saved to {report_path}")
        self._refresh()

    @on(Button.Pressed, "#export-report-btn")
    def _export(self) -> None:
        self.dismiss()
        self.app.push_screen(
            SaveSessionScreen(current_name="./exported_report.md"),
            self.app._handle_export_report
        )

    @on(Button.Pressed, "#close-reports")
    def _close(self) -> None:
        self.dismiss()

    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss()


class ToolPanel(ModalScreen[None]):
    """Modal for managing and verifying pentesting tools."""
    DEFAULT_CSS = f"""
    ToolPanel {{
        align: center middle;
        background: #000000aa;
    }}
    #tool-modal {{
        width: 90;
        height: 26;
        padding: 1 2;
        background: {BG_PANEL};
        border: tall {FG_DIM};
        layout: vertical;
    }}
    #tool-title {{
        color: {FG};
        text-style: bold;
        padding-bottom: 1;
    }}
    #tool-options {{
        height: auto;
        layout: horizontal;
        padding-bottom: 1;
    }}
    #tool-list {{
        height: 1fr;
        border: solid {FG_DIM};
        background: {BG};
        overflow-y: auto;
        padding: 0 1;
    }}
    #tool-actions {{
        height: auto;
        padding-top: 1;
    }}
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="tool-modal"):
            yield Static("Pentesting Tools Registry", id="tool-title")
            with Horizontal(id="tool-options"):
                yield Button("Verify All Tools", id="verify-tools-btn", variant="primary")
                yield Button("Update All Tools", id="update-tools-btn")
            yield OptionList(id="tool-list")
            with Horizontal(id="tool-actions"):
                yield Button("Close", id="close-tools")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        ol = self.query_one("#tool-list", OptionList)
        ol.clear_options()
        
        from redforge.tools import ToolRegistry, ToolManager
        tm = ToolManager()
        for name, tool in ToolRegistry.get_all_tools().items():
            status = tm.check_tool(name)
            status_str = f"[green]Installed ({status.version})[/green]" if status.installed else "[red]Not Installed[/red]"
            ol.add_option(Option(f"🛠️  {name:<12} | {status_str:<25} | {tool.description}"))

    @on(Button.Pressed, "#verify-tools-btn")
    def _verify(self) -> None:
        from redforge.tools import ToolManager
        tm = ToolManager()
        report = tm.get_status_report()
        self.app.toast_mgr.show(f"Verified: {report['installed']}/{report['total_tools']} tools installed.", "info")
        self._refresh()

    @on(Button.Pressed, "#update-tools-btn")
    def _update(self) -> None:
        from redforge.tools import ToolManager
        tm = ToolManager()
        updated = 0
        for name in tm.installed_tools:
            status = tm.check_tool(name)
            if status.installed:
                tm.update_tool(name)
                updated += 1
        self.app.toast_mgr.show(f"Updated {updated} tools.", "success")
        self._refresh()

    @on(Button.Pressed, "#close-tools")
    def _close(self) -> None:
        self.dismiss()

    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss()


class MemoryScreen(ModalScreen[None]):
    """Modal for managing and searching Agent memory."""
    DEFAULT_CSS = f"""
    MemoryScreen {{
        align: center middle;
        background: #000000aa;
    }}
    #memory-modal {{
        width: 88;
        height: 28;
        padding: 1 2;
        background: {BG_PANEL};
        border: tall {FG_DIM};
        layout: vertical;
    }}
    #memory-title {{
        color: {FG};
        text-style: bold;
        padding-bottom: 1;
    }}
    #memory-stats {{
        padding-bottom: 1;
        color: {FG};
    }}
    #memory-options {{
        height: auto;
        layout: horizontal;
        padding-bottom: 1;
    }}
    #memory-search {{
        border: none;
        border-bottom: solid {FG_DIM};
        background: {BG_PANEL};
        color: {FG};
        padding: 0 1;
        margin-bottom: 1;
    }}
    #memory-results {{
        height: 1fr;
        border: solid {FG_DIM};
        background: {BG};
        overflow-y: auto;
        padding: 0 1;
    }}
    #memory-actions {{
        height: auto;
        padding-top: 1;
    }}
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="memory-modal"):
            yield Static("Memory Manager", id="memory-title")
            yield Static("Loading stats…", id="memory-stats")
            with Horizontal(id="memory-options"):
                yield Button("Rebuild Index", id="rebuild-mem-btn", variant="primary")
                yield Button("Clear Memory", id="clear-mem-btn")
            yield Input(placeholder="Search memory…", id="memory-search")
            yield OptionList(id="memory-results")
            with Horizontal(id="memory-actions"):
                yield Button("Close", id="close-memory")

    def on_mount(self) -> None:
        self._refresh_stats()
        self.query_one("#memory-search", Input).focus()

    def _refresh_stats(self) -> None:
        from redforge.core.config import get_settings
        from redforge.memory.memory_manager import WorkspaceMemoryManager
        settings = get_settings()
        mm = WorkspaceMemoryManager("default", settings.memory.persist_dir, settings.memory.vector_db)
        stats = mm.get_stats()
        self.query_one("#memory-stats", Static).update(
            f"Vector Store: {'Available' if stats.get('vector_store_available') else 'Unavailable'}  |  "
            f"Total Sessions: {stats.get('total_sessions', 0)}  |  "
            f"Findings: {stats.get('total_findings', 0)}  |  "
            f"Notes: {stats.get('total_notes', 0)}"
        )

    @on(Button.Pressed, "#rebuild-mem-btn")
    def _rebuild(self) -> None:
        from redforge.core.config import get_settings
        from redforge.memory.memory_manager import WorkspaceMemoryManager
        settings = get_settings()
        mm = WorkspaceMemoryManager("default", settings.memory.persist_dir, settings.memory.vector_db)
        mm.clear()
        
        # Add current messages and findings
        messages = self.app.db.get_messages(self.app.session_id)
        findings = self.app.db.get_findings(self.app.session_id)
        for m in messages:
            mm.add_session(m["role"], m["content"], {"timestamp": m.get("timestamp")})
        for f in findings:
            mm.add_finding(f["type"], f["title"], f["description"], f["severity"], f["target"], f.get("evidence"))
            
        self.app.toast_mgr.show("Memory index rebuilt successfully", "success")
        self._refresh_stats()

    @on(Button.Pressed, "#clear-mem-btn")
    def _clear(self) -> None:
        from redforge.core.config import get_settings
        from redforge.memory.memory_manager import WorkspaceMemoryManager
        settings = get_settings()
        mm = WorkspaceMemoryManager("default", settings.memory.persist_dir, settings.memory.vector_db)
        mm.clear()
        self.app.toast_mgr.show("Memory cleared successfully", "info")
        self._refresh_stats()

    @on(Input.Changed, "#memory-search")
    def _search(self, event: Input.Changed) -> None:
        val = event.value.strip()
        ol = self.query_one("#memory-results", OptionList)
        ol.clear_options()
        if not val:
            return
            
        from redforge.core.config import get_settings
        from redforge.memory.memory_manager import WorkspaceMemoryManager
        settings = get_settings()
        mm = WorkspaceMemoryManager("default", settings.memory.persist_dir, settings.memory.vector_db)
        results = mm.search(val, limit=5)
        if not results:
            ol.add_option(Option("No results found.", disabled=True))
        else:
            for r in results:
                ol.add_option(Option(f"🔍 [score: {r.score:.2f}] {r.content}"))

    @on(Button.Pressed, "#close-memory")
    def _close(self) -> None:
        self.dismiss()

    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss()


class HelpDialog(ModalScreen[None]):
    """Modal showing help, modes, and keyboard shortcuts."""
    DEFAULT_CSS = f"""
    HelpDialog {{
        align: center middle;
        background: #000000aa;
    }}
    #help-modal {{
        width: 80;
        height: auto;
        padding: 1 2;
        background: {BG_PANEL};
        border: tall {FG_DIM};
        layout: vertical;
    }}
    #help-title {{
        color: {FG};
        text-style: bold;
        padding-bottom: 1;
    }}
    .help-section {{
        color: {FG};
        text-style: bold;
        padding-top: 1;
        padding-bottom: 0;
    }}
    .help-row {{
        color: {FG_MUTED};
        padding-left: 2;
    }}
    #help-actions {{
        height: auto;
        padding-top: 1;
        align: right middle;
    }}
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="help-modal"):
            yield Static("RedForge TUI Help & Shortcuts", id="help-title")
            
            yield Static("Keyboard Shortcuts:", classes="help-section")
            yield Static("[bold]Ctrl+P[/bold]  → Open Command Palette", classes="help-row")
            yield Static("[bold]Ctrl+S[/bold]  → Save Current Session", classes="help-row")
            yield Static("[bold]Ctrl+R[/bold]  → Open Reports Screen", classes="help-row")
            yield Static("[bold]Ctrl+F[/bold]  → Open Findings Screen", classes="help-row")
            yield Static("[bold]Ctrl+M[/bold]  → Open Memory Screen", classes="help-row")
            yield Static("[bold]Ctrl+L[/bold]  → Clear Conversation", classes="help-row")
            yield Static("[bold]Ctrl+Q[/bold]  → Quit TUI Application", classes="help-row")
            yield Static("[bold]Ctrl+B[/bold]  → Toggle Left Sidebar", classes="help-row")
            yield Static("[bold]Ctrl+K[/bold]  → Cancel Current Running Task", classes="help-row")
            yield Static("[bold]Escape[/bold]  → Refocus Input Box", classes="help-row")
            
            yield Static("Available Slash Commands (in Input Box):", classes="help-section")
            yield Static("[bold]/mode[/bold]      → Change operational mode (bugbounty, ctf, etc.)", classes="help-row")
            yield Static("[bold]/target[/bold]    → Set scan target IP/domain", classes="help-row")
            yield Static("[bold]/autonomy[/bold]  → Set autonomy (manual, partial, full)", classes="help-row")
            yield Static("[bold]/approved[/bold]  → Approve the planned tool execution", classes="help-row")
            
            yield Static("Input Formats:", classes="help-section")
            yield Static("[bold]@filename[/bold] → Insert/attach a workspace file's content", classes="help-row")
            yield Static("[bold]!command[/bold]  → Execute a local bash shell command", classes="help-row")
            
            with Horizontal(id="help-actions"):
                yield Button("OK", id="close-help-btn", variant="primary")

    @on(Button.Pressed, "#close-help-btn")
    def _close(self) -> None:
        self.dismiss()

    async def on_key(self, event: events.Key) -> None:
        if event.key in ("escape", "enter"):
            self.dismiss()


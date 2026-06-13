"""
RedForge TUI — Widget Library
VimInput, GhostText, SpinnerWidget, ToolBlock, DiffBlock, FooterBar.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive

from redforge.llm.catalog import DEFAULT_MODELS
from textual.widget import Widget
from textual.widgets import Input, Static

from rich.markup import escape

from redforge.tui.renderer import (
    ACCENT, BG, BG_PANEL, BORDER, FG, FG_DIM, FG_MUTED,
    MODE_COLOR, MODE_LABEL, MODES, SEV_COLOR, _e, fmt_k,
)

SPINNER = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


# ─── VimInput ────────────────────────────────────────────

class VimInput(Widget):
    """
    Vim-style input widget.
    Modes: insert (default), normal, visual.
    Keybindings in normal mode: i/a/A→insert, dd→clear, 0→home, $→end.
    Shift+Enter → newline in buffer (multiline).
    """

    DEFAULT_CSS = f"""
    VimInput {{
        height: 3;
        background: {BG_PANEL};
        border-top: tall {FG_DIM};
        layout: horizontal;
        align: left middle;
    }}
    #vi-mode  {{ width: 5; text-style: bold; padding: 0 0 0 1; }}
    #vi-input {{
        width: 1fr;
        background: {BG_PANEL};
        border: none;
        color: {FG};
        padding: 0 0;
    }}
    #vi-ghost {{ width: auto; color: {FG_DIM}; padding: 0 0; }}
    #vi-right {{ width: 18; color: {FG_DIM}; padding: 0 1; text-align: right; }}
    """

    vim_mode: reactive[str] = reactive("insert")  # insert | normal | visual
    app_mode: reactive[str] = reactive("bugbounty")
    tokens: reactive[int] = reactive(0)
    ghost: reactive[str] = reactive("")

    _history: List[str] = []
    _hist_idx: int = -1
    _multiline_buf: List[str] = []

    # Ghost text suggestions
    _suggestions: Dict[str, str] = {
        "/mo": "de bugbounty",
        "/ta": "rget ",
        "/au": "tonomy partial",
        "/wo": "rkspace default",
        "/cl": "ear",
        "/he": "lp",
        "/sk": "ills",
        "/st": "atus",
        "/fi": "ndings",
        "/re": "port",
    }

    class Submitted(Message):
        """Posted when the user submits the VimInput buffer."""

        def __init__(self, sender: "VimInput", value: str) -> None:
            super().__init__()
            self.value = value

    def compose(self) -> ComposeResult:
        yield Static("[I]", id="vi-mode")
        yield Input(placeholder="message, /command, !shell, or @file…", id="vi-input")
        yield Static("", id="vi-ghost")
        yield Static("", id="vi-right")

    def on_mount(self) -> None:
        self.query_one("#vi-input", Input).focus()
        self._refresh_mode_badge()
        self._refresh_right()

    # ── mode display ──

    def watch_vim_mode(self, mode: str) -> None:
        self._refresh_mode_badge()

    def watch_app_mode(self, mode: str) -> None:
        self._refresh_mode_badge()

    def _refresh_mode_badge(self) -> None:
        colors = {"insert": "#00cc66", "normal": "#4488ff", "visual": "#ff8800"}
        labels = {"insert": " INS ", "normal": " NOR ", "visual": " VIS "}
        c = colors.get(self.vim_mode, FG_MUTED)
        lbl = labels.get(self.vim_mode, " ??? ")
        try:
            self.query_one("#vi-mode", Static).update(f"[bold {BG} on {c}]{lbl}[/]")
            self.query_one("#vi-mode", Static).styles.width = 7
        except NoMatches:
            pass

    def watch_tokens(self, t: int) -> None:
        self._refresh_right()

    def _refresh_right(self) -> None:
        try:
            self.query_one("#vi-right", Static).update(
                f"[{FG_DIM}]{fmt_k(self.tokens)} tok[/]"
            )
        except NoMatches:
            pass

    # ── ghost text ──

    def on_input_changed(self, event: Input.Changed) -> None:
        val = event.value
        # Update prompt colour
        try:
            mc = MODE_COLOR.get(self.app_mode, ACCENT)
            badge = self.query_one("#vi-mode", Static)
            if self.vim_mode == "insert":
                if val.startswith("/"):
                    badge.update(f"[bold #00d4ff]/[/]")
                elif val.startswith("!"):
                    badge.update(f"[bold #ffcc00]![/]")
                else:
                    self._refresh_mode_badge()
        except NoMatches:
            pass

        if self.vim_mode == "insert":
            inp = self._get_input()
            if inp:
                if val == "/":
                    opener = getattr(self.app, "open_command_palette", None)
                    if callable(opener):
                        self.app.call_later(opener, "/")
                
                cursor = inp.cursor_position
                if 0 < cursor <= len(val) and val[cursor - 1] == "@":
                    if cursor == 1 or val[cursor - 2].isspace():
                        opener = getattr(self.app, "open_file_mention_picker", None)
                        if callable(opener):
                            # Call later to avoid interfering with current event processing
                            self.app.call_later(opener, "")

        # Ghost text
        ghost = ""
        if val and self.vim_mode == "insert":
            for prefix, suffix in self._suggestions.items():
                if val == prefix or (val.startswith("/") and val[1:].startswith(prefix[1:]) and len(val) < len(prefix) + len(suffix)):
                    if val.startswith(prefix):
                        ghost = suffix
                    break
        try:
            self.query_one("#vi-ghost", Static).update(
                f"[{FG_DIM}]{ghost}[/]" if ghost else ""
            )
        except NoMatches:
            pass
        self.ghost = ghost

    # ── key handling for vim modes ──

    def on_key(self, event) -> None:
        inp = self._get_input()
        if inp is None:
            return

        if self.vim_mode == "normal":
            key = event.key
            if key == "i":
                self.vim_mode = "insert"
                inp.focus()
                event.prevent_default()
            elif key == "a":
                self.vim_mode = "insert"
                inp.focus()
                event.prevent_default()
            elif key == "shift+a" or key == "A":
                self.vim_mode = "insert"
                inp.cursor_position = len(inp.value)
                inp.focus()
                event.prevent_default()
            elif key == "d":
                # Simple dd → wait for second d (simplified: single press clears)
                inp.value = ""
                event.prevent_default()
            elif key == "0":
                inp.cursor_position = 0
                event.prevent_default()
            elif key == "dollar" or key == "$":
                inp.cursor_position = len(inp.value)
                event.prevent_default()
            return

        # Insert mode
        if event.key == "enter":
            value = inp.value
            self.clear_input()
            self.post_message(self.Submitted(self, value))
            event.prevent_default()
            event.stop()
            return

        if event.key == "escape":
            if inp.value:
                self.vim_mode = "normal"
            event.prevent_default()
            return

        if event.key == "tab":
            mention_query = self.active_mention_query()
            if mention_query is not None:
                opener = getattr(self.app, "open_file_mention_picker", None)
                if callable(opener):
                    opener(mention_query)
                    event.prevent_default()
                    return

            # Tab when input starts with '/' -> open command palette
            if inp.value.startswith("/"):
                opener = getattr(self.app, "open_command_palette", None)
                if callable(opener):
                    val = inp.value
                    self.app.call_later(opener, val)
                    event.prevent_default()
                    event.stop()
                    return

            # Tab → accept ghost text
            if self.ghost:
                inp.value = inp.value + self.ghost
                inp.cursor_position = len(inp.value)
                self.ghost = ""
                event.prevent_default()
                return

    # ── history ──

    def push_history(self, s: str) -> None:
        if s and (not self._history or self._history[-1] != s):
            self._history.append(s)
        self._hist_idx = -1

    def recall_prev(self) -> str:
        if not self._history:
            return ""
        if self._hist_idx < len(self._history) - 1:
            self._hist_idx += 1
        return self._history[-(self._hist_idx + 1)]

    def recall_next(self) -> str:
        if self._hist_idx > 0:
            self._hist_idx -= 1
            return self._history[-(self._hist_idx + 1)]
        self._hist_idx = -1
        return ""

    # ── utility ──

    def clear_input(self) -> None:
        try:
            inp = self.query_one("#vi-input", Input)
            inp.value = ""
            inp.cursor_position = 0
        except NoMatches:
            pass

    def set_value(self, v: str) -> None:
        try:
            inp = self.query_one("#vi-input", Input)
            inp.value = v
            inp.cursor_position = len(v)
        except NoMatches:
            pass

    def focus_input(self) -> None:
        if self.vim_mode == "normal":
            self.vim_mode = "insert"
        try:
            self.query_one("#vi-input", Input).focus()
        except NoMatches:
            pass

    def _get_input(self) -> Optional[Input]:
        try:
            return self.query_one("#vi-input", Input)
        except NoMatches:
            return None

    def replace_active_mention(self, value: str) -> None:
        inp = self._get_input()
        if inp is None:
            return
        text = inp.value
        cursor = inp.cursor_position
        start = cursor
        while start > 0 and not text[start - 1].isspace():
            start -= 1
        if start < len(text) and text[start:start + 1] == "@":
            inp.value = text[:start] + value + text[cursor:]
            inp.cursor_position = start + len(value)
        else:
            suffix = "" if not text or text.endswith(" ") else " "
            inp.value = text + suffix + value
            inp.cursor_position = len(inp.value)

    def active_mention_query(self) -> Optional[str]:
        inp = self._get_input()
        if inp is None:
            return None
        text = inp.value
        cursor = inp.cursor_position
        start = cursor
        while start > 0 and not text[start - 1].isspace():
            start -= 1
        token = text[start:cursor]
        if token.startswith("@"):
            return token[1:]
        return None

    @property
    def value(self) -> str:
        inp = self._get_input()
        return inp.value if inp else ""


# ─── SpinnerWidget ───────────────────────────────────────

class SpinnerWidget(Widget):
    """Animated braille spinner with label."""

    DEFAULT_CSS = f"""
    SpinnerWidget {{ height: 1; color: {FG_MUTED}; padding: 0 2; }}
    """

    label: reactive[str] = reactive("thinking…")
    active: reactive[bool] = reactive(False)
    _frame: int = 0

    def render(self) -> str:
        if not self.active:
            return ""
        frame = SPINNER[self._frame % len(SPINNER)]
        return f"[bold #ffcc00]{frame}[/]  [{FG_MUTED}]{self.label}[/]"

    def tick(self) -> None:
        if self.active:
            self._frame += 1
            self.refresh()


# ─── ToolBlock ───────────────────────────────────────────

class ToolBlock(Widget):
    """
    Collapsible tool execution block.
    Click header to expand/collapse output.
    """

    DEFAULT_CSS = f"""
    ToolBlock {{
        height: auto;
        margin: 0 1;
        padding: 0;
        transition: opacity 300ms, offset 300ms in_out_cubic;
    }}
    """

    tool_name: reactive[str] = reactive("")
    command: reactive[str] = reactive("")
    output: reactive[str] = reactive("")
    status: reactive[str] = reactive("running")  # running | done | failed
    elapsed: reactive[float] = reactive(0.0)
    expanded: reactive[bool] = reactive(False)
    _frame: int = 0

    def render(self) -> str:
        w = 54
        name = self.tool_name or "tool"
        sc = {"running": "#ffcc00", "done": "#00cc66", "failed": "#ff3333"}.get(self.status, FG_DIM)
        si = {"running": SPINNER[self._frame % len(SPINNER)], "done": "✔", "failed": "✘"}.get(self.status, "?")

        top = f"[{FG_DIM}]┏━━ [bold {ACCENT}]tool: {name.upper()}[/] {'━' * max(0, w - len(name) - 9)}┓[/]"
        cmd = f"[{FG_DIM}]┃[/]  [dim #888888]$ {_e(self.command[:w - 4])}[/dim]"

        if self.status == "running":
            body = f"[{FG_DIM}]┃[/]  [bold {sc}]{si}[/]  [dim]running… {self.elapsed:.1f}s[/dim]"
            toggle = ""
        else:
            toggle_label = "▼ collapse" if self.expanded else "▶ expand"
            toggle = f"[{FG_DIM}]┣━━ [{FG_MUTED}]{toggle_label}[/] {'━' * (w - len(toggle_label) + 1)}┫[/]"
            if self.expanded and self.output:
                out_lines = []
                for line in self.output.strip().splitlines()[:25]:
                    out_lines.append(f"[{FG_DIM}]┃[/]  [{FG_MUTED}]{_e(line[:w])}[/]")
                body = "\n".join(out_lines)
            else:
                body = ""

        footer = f"[{FG_DIM}]┃[/]  [bold {sc}]{si} {self.status.upper()}[/]  [dim]{self.elapsed:.2f}s[/dim]"
        bot = f"[{FG_DIM}]┗{'━' * (w + 2)}┛[/]"

        parts = [top, cmd]
        if toggle:
            parts.append(toggle)
        if body:
            parts.append(body)
        parts.extend([footer, bot])
        return "\n".join(parts)

    def on_click(self) -> None:
        if self.status != "running":
            self.expanded = not self.expanded

    def tick(self) -> None:
        if self.status == "running":
            self._frame += 1
            self.refresh()


# ─── DiffBlock ───────────────────────────────────────────

class DiffBlock(Widget):
    """Unified diff viewer with ± colour coding and collapse toggle."""

    DEFAULT_CSS = f"""
    DiffBlock {{
        height: auto;
        margin: 0 1;
    }}
    """

    title: reactive[str] = reactive("diff")
    diff_text: reactive[str] = reactive("")
    expanded: reactive[bool] = reactive(True)

    def render(self) -> str:
        w = 54
        top = f"[{FG_DIM}]┌── [bold {ACCENT}]{_e(self.title)}[/] {'─' * max(0, w - len(self.title) - 5)}┐[/]"

        if not self.expanded:
            bot = f"[{FG_DIM}]└── [{FG_MUTED}]▸ click to expand[/] {'─' * (w - 16)}┘[/]"
            return f"{top}\n{bot}"

        lines = []
        for raw in self.diff_text.splitlines()[:40]:
            safe = _e(raw[:w])
            if raw.startswith("+"):
                lines.append(f"[{FG_DIM}]│[/] [bold #00cc66]{safe}[/]")
            elif raw.startswith("-"):
                lines.append(f"[{FG_DIM}]│[/] [bold #ff4444]{safe}[/]")
            elif raw.startswith("@@"):
                lines.append(f"[{FG_DIM}]│[/] [bold #00d4ff]{safe}[/]")
            else:
                lines.append(f"[{FG_DIM}]│[/] {safe}")

        bot = f"[{FG_DIM}]└{'─' * (w + 2)}┘[/]"
        return "\n".join([top] + lines + [bot])

    def on_click(self) -> None:
        self.expanded = not self.expanded


# ─── FooterBar ───────────────────────────────────────────

class FooterBar(Widget):
    """Bottom status bar: model, tokens, cost, latency."""

    DEFAULT_CSS = f"""
    FooterBar {{
        height: 1;
        background: {BG_PANEL};
        border-top: tall {FG_DIM};
        layout: horizontal;
        padding: 0 1;
        transition: background 500ms;
    }}
    FooterBar > Static {{ width: auto; height: 1; }}
    #fb-left  {{ color: {FG_MUTED}; width: 1fr; }}
    #fb-model {{ color: {ACCENT}; padding: 0 2; }}
    #fb-tokens {{ color: {FG_DIM}; padding: 0 1; border-left: tall {FG_DIM}; }}
    #fb-cost  {{ color: {FG_DIM}; padding: 0 1; }}
    #fb-latency {{ color: {FG_DIM}; padding: 0 1; border-left: tall {FG_DIM}; }}
    """

    model: reactive[str] = reactive(DEFAULT_MODELS["gemini"])
    tokens: reactive[int] = reactive(0)
    latency_ms: reactive[float] = reactive(0.0)
    mode: reactive[str] = reactive("bugbounty")

    def compose(self) -> ComposeResult:
        yield Static("", id="fb-left")
        yield Static("", id="fb-model")
        yield Static("", id="fb-tokens")
        yield Static("", id="fb-cost")
        yield Static("", id="fb-latency")

    def on_mount(self) -> None:
        self._refresh()

    def watch_model(self, m: str) -> None:
        self._refresh()

    def watch_tokens(self, t: int) -> None:
        self._refresh()
        self.styles.animate("background", "#2a2a2a", duration=0.1, final_value=BG_PANEL)

    def watch_latency_ms(self, l: float) -> None:
        self._refresh()

    def watch_mode(self, m: str) -> None:
        self._refresh()

    def _refresh(self) -> None:
        mc = MODE_COLOR.get(self.mode, ACCENT)
        cost = self.tokens * 0.0000007
        try:
            self.query_one("#fb-left", Static).update(
                f"[bold {mc}]^B[/] Side  "
                f"[bold {mc}]^L[/] Clear  "
                f"[bold {mc}]^K[/] Kill  "
                f"[bold {mc}]TAB[/] Menu"
            )
            self.query_one("#fb-model", Static).update(f"[bold {ACCENT}]▶[/] {_e(self.model)}")
            self.query_one("#fb-tokens", Static).update(f"{fmt_k(self.tokens)} TOK")
            self.query_one("#fb-cost", Static).update(f"[dim]${cost:.4f}[/]")
            lat = f"{self.latency_ms:.0f}ms" if self.latency_ms else "—"
            self.query_one("#fb-latency", Static).update(f"[bold]{lat}[/]")
        except NoMatches:
            pass

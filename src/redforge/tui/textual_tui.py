"""RedForge Textual TUI (v3) — a Claude Code-style terminal interface.

A clean, linear, conversational terminal UI wired to :class:`RedForgeAgent`,
modeled on the look & feel of Claude Code: a welcome card, inline Markdown
replies, ``⏺`` / ``⎿`` tool-call lines, a rounded input box with a ``>``
caret, a playful "thinking" spinner, and a minimal bottom hint bar.

Launch with::

    redforge-tui
    python -m redforge.tui.textual_tui
    python -c "from redforge.tui import launch_textual; launch_textual()"
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any

from rich.markdown import Markdown as RichMarkdown
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Input, Static

# ---------------------------------------------------------------------------
# Palette (warm, Claude Code-ish: clay accent on a near-black canvas)
# ---------------------------------------------------------------------------
ACCENT = "#d97757"  # clay / coral accent
TEXT = "#e6e1d7"
DIM = "#8a8577"
MUTED = "#6b6659"
SUCCESS = "#8bbf9f"
ERROR = "#e07a5f"
BG = "#1a1915"
SURFACE = "#211f1a"

MODES = ["bugbounty", "ctf", "learning", "coding", "android", "research"]
PROVIDERS = ["ollama", "openai", "gemini", "groq", "anthropic"]
COMMANDS = ["/help", "/mode", "/model", "/workspace", "/copy", "/clear", "/quit"]

SPIN_SYMBOLS = ["✻", "✶", "✳", "✦", "✧", "✦", "✳", "✶"]
SPIN_WORDS = [
    "Forging",
    "Thinking",
    "Reasoning",
    "Scanning",
    "Computing",
    "Pondering",
    "Analyzing",
    "Cerebrating",
    "Reconnoitring",
]

SHORTCUTS = f"""[{ACCENT} bold]Keyboard shortcuts[/]

  [bold]Enter[/]        send message
  [bold]/[/]            slash command   ([dim]Tab to complete[/])
  [bold]![/]            run a shell command
  [bold]Esc[/]          interrupt a running task / clear input
  [bold]Ctrl+Y[/]       copy last response to clipboard
  [bold]Ctrl+O[/]       cycle mode
  [bold]Ctrl+L[/]       clear the conversation
  [bold]Ctrl+C[/]       quit

[{ACCENT} bold]Slash commands[/]

  /help                 show this panel
  /mode <name>          {", ".join(MODES)}
  /model <provider>     {", ".join(PROVIDERS)}
  /workspace <path>     set working directory label
  /copy [all]           copy last response (or whole transcript)
  /clear                clear the conversation
  /quit                 exit RedForge

[{DIM}]Press Esc or Enter to close.[/]"""


class HelpScreen(ModalScreen):
    """Modal shortcuts panel (opened with ? / F1 / /help)."""

    CSS = f"""
    HelpScreen {{ align: center middle; background: rgba(0,0,0,0.6); }}
    #help-box {{
        width: 70; height: auto; max-height: 90%;
        background: {SURFACE}; color: {TEXT};
        border: round {ACCENT}; padding: 1 2;
    }}
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("enter", "close", "Close"),
        Binding("q", "close", "Close"),
        Binding("question_mark", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="help-box"):
            yield Static(SHORTCUTS)

    def action_close(self) -> None:
        self.dismiss()


class RedForgeTUI(App):
    """RedForge Textual application in a Claude Code-style layout."""

    TITLE = "RedForge"

    CSS = f"""
    Screen {{ background: {BG}; color: {TEXT}; layers: base; }}

    #conversation {{
        width: 1fr; height: 1fr;
        padding: 1 2 0 2;
        background: {BG};
    }}

    #welcome {{
        border: round {ACCENT};
        padding: 0 2;
        margin: 0 0 1 0;
        color: {TEXT};
    }}

    .block {{ margin: 0 0 1 0; }}
    .user {{ color: {DIM}; }}
    .assistant {{ color: {TEXT}; }}
    .note {{ color: {MUTED}; }}
    .tool {{ color: {ACCENT}; }}
    .result {{ color: {DIM}; padding: 0 0 0 2; }}
    .result-error {{ color: {ERROR}; padding: 0 0 0 2; }}
    .finding {{ color: {SUCCESS}; }}
    .err {{ color: {ERROR}; }}

    #thinking {{
        height: 1;
        padding: 0 2;
        color: {ACCENT};
        display: none;
    }}
    #thinking.active {{ display: block; }}

    #input-box {{
        height: 3;
        margin: 0 2;
        border: round {MUTED};
        background: {SURFACE};
    }}
    #input-box:focus-within {{ border: round {ACCENT}; }}
    #caret {{ width: 2; color: {ACCENT}; content-align: center middle; }}
    #command-input {{
        border: none; background: {SURFACE}; height: 1fr;
        padding: 0;
    }}

    #hint {{ height: 1; padding: 0 3; }}
    #hint-left {{ width: 1fr; color: {MUTED}; }}
    #hint-right {{ width: auto; color: {MUTED}; }}
    """

    BINDINGS = [
        Binding("ctrl+l", "clear", "Clear", show=False),
        Binding("ctrl+o", "cycle_mode", "Mode", show=False),
        Binding("ctrl+y", "copy_last", "Copy", show=False),
        Binding("f1", "help", "Help", show=False),
        Binding("escape", "interrupt_or_clear", "Esc", show=False),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("tab", "autocomplete", "Complete", show=False, priority=True),
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.agent = None
        self.mode = "bugbounty"
        self.model_name = "connecting…"
        self.workspace = "~"
        self.total_tokens = 0
        self.live_tokens = 0
        self.findings_count = 0
        self.history: list[str] = []
        self.hist_index = 0
        self.transcript: list[str] = []
        self.last_assistant_text = ""
        self._current_assistant: Static | None = None
        self._assistant_text = ""
        self._turn_rendered = False
        self._busy = False
        self._spin = 0
        self._spin_word = SPIN_WORDS[0]
        self._spin_timer = None
        self._start_time = 0.0

    # -- layout -------------------------------------------------------------
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="conversation"):
            yield Static(self._welcome_text(), id="welcome")
        yield Static("", id="thinking")
        with Horizontal(id="input-box"):
            yield Static(">", id="caret")
            yield Input(placeholder='Try "scan example.com" or ask anything…', id="command-input")
        with Horizontal(id="hint"):
            yield Static("", id="hint-left")
            yield Static("", id="hint-right")

    def _welcome_text(self) -> str:
        return (
            f"[{ACCENT} bold]✻ Welcome to RedForge[/]\n\n"
            f"[{DIM}]Autonomous security agent — and a general-purpose assistant.[/]\n"
            f"[{DIM}]/help for shortcuts · ! to run shell · Ctrl+Y to copy[/]\n\n"
            f"[{MUTED}]cwd:[/] {self.workspace}    [{MUTED}]mode:[/] {self.mode}"
        )

    async def on_mount(self) -> None:
        self._init_agent()
        self.set_focus(self.query_one("#command-input", Input))
        self.update_hint()
        self._note("Connecting to the agent…")

    # -- agent lifecycle ----------------------------------------------------
    @work(thread=True)
    def _init_agent(self, provider: str | None = None) -> None:
        try:
            from redforge.core.agent import RedForgeAgent

            agent = RedForgeAgent(llm_provider=provider) if provider else RedForgeAgent()
            try:
                status = agent.get_status()
            except Exception:  # pragma: no cover
                status = {}
            self.call_from_thread(self._agent_ready, agent, status, provider)
        except Exception as exc:  # pragma: no cover
            self.call_from_thread(self._error, f"Failed to initialize agent: {exc}")

    def _agent_ready(self, agent: Any, status: dict[str, Any], switched: str | None) -> None:
        self.agent = agent
        self._register_agent_events()
        self.model_name = str(status.get("llm_provider", switched or "unknown"))
        self.update_hint()
        self._refresh_welcome()
        if switched:
            self._note(f"Switched provider → {switched} ({self.model_name}).")
        else:
            self._note(f"Ready · {self.model_name} · {status.get('skills_total', 0)} skills")

    def _register_agent_events(self) -> None:
        a = self.agent
        if a is None:
            return
        a.on("assistant_start", self._on_assistant_start)
        a.on("token", self._on_token)
        a.on("assistant_end", self._on_assistant_end)
        a.on("tool_start", self._on_tool_start)
        a.on("tool_end", self._on_tool_end)
        a.on("finding", self._on_finding)
        a.on("error", self._on_agent_error)

    # -- agent events -------------------------------------------------------
    def _on_assistant_start(self, payload: dict[str, Any]) -> None:
        self._start_assistant()

    def _on_token(self, payload: dict[str, Any]) -> None:
        token = payload.get("token", "")
        if self._current_assistant is None:
            self._start_assistant()
        self._turn_rendered = True
        self._assistant_text += token
        self.live_tokens += 1
        if self._current_assistant is not None:
            self._current_assistant.update(self._assistant_text)
        self._scroll()

    def _on_assistant_end(self, payload: dict[str, Any]) -> None:
        content = payload.get("content", "")
        if self._current_assistant is None and content:
            self._append_markdown(content)
            self._turn_rendered = True
        elif self._current_assistant is not None:
            final = content or self._assistant_text
            if final:
                self._current_assistant.update(self._md(final))
                self._turn_rendered = True
                self.transcript.append(final)
                self.last_assistant_text = final
        self._current_assistant = None
        self._assistant_text = ""

    def _on_tool_start(self, payload: dict[str, Any]) -> None:
        tool = str(payload.get("tool", "tool"))
        command = payload.get("command", "")
        label = f"⏺ {tool}" + (f"([italic]{command}[/])" if command else "")
        self._append(label, "tool")

    def _on_tool_end(self, payload: dict[str, Any]) -> None:
        stdout, error = self._extract_result(payload.get("result"))
        if error:
            self._append(f"⎿  {error}", "result-error")
        else:
            out = (stdout or "").strip()
            if out:
                lines = out.splitlines()
                head = lines[0]
                extra = len(lines) - 1
                tail = f"  [+{extra} lines]" if extra > 0 else ""
                if len(head) > 200:
                    head = head[:200] + "…"
                self._append(f"⎿  {head}{tail}", "result")

    def _on_finding(self, payload: dict[str, Any]) -> None:
        self.findings_count += 1
        self._append(f"⏺ finding: {self._finding_title(payload.get('finding'))}", "finding")

    def _on_agent_error(self, payload: dict[str, Any]) -> None:
        self._error(str(payload.get("message", "unknown error")))

    # -- input --------------------------------------------------------------
    @on(Input.Submitted, "#command-input")
    def _on_submit(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        self.history.append(text)
        self.hist_index = len(self.history)
        if text.startswith("/"):
            self._handle_command(text)
        elif text.startswith("!"):
            self._run_shell(text[1:].strip())
        else:
            self._user(text)
            if self.agent is None:
                self._error("Agent is still connecting — one moment.")
                return
            if self._busy:
                self._note("Busy — press Esc to interrupt.")
                return
            self.process_input(text)

    def action_autocomplete(self) -> None:
        inp = self.query_one("#command-input", Input)
        value = inp.value
        if not value.startswith("/") or " " in value:
            return
        matches = [c for c in COMMANDS if c.startswith(value)]
        if not matches:
            return
        if len(matches) == 1:
            inp.value = matches[0] + " "
        else:
            from os.path import commonprefix

            prefix = commonprefix(matches)
            if len(prefix) > len(value):
                inp.value = prefix
            else:
                self._note("Commands: " + "  ".join(matches))
                return
        inp.cursor_position = len(inp.value)

    def on_key(self, event) -> None:
        inp = self.query_one("#command-input", Input)
        if not inp.has_focus or inp.value:
            return
        if event.key == "up" and self.history:
            self.hist_index = max(0, self.hist_index - 1)
            inp.value = self.history[self.hist_index]
            event.stop()
        elif event.key == "down" and self.history:
            self.hist_index = min(len(self.history), self.hist_index + 1)
            inp.value = (
                "" if self.hist_index >= len(self.history) else self.history[self.hist_index]
            )
            event.stop()

    @work(exclusive=True)
    async def process_input(self, text: str) -> None:
        self._busy = True
        self._turn_rendered = False
        self.live_tokens = 0
        self._start_spinner()
        start = time.monotonic()
        try:
            state = await self.agent.run(text, mode=self.mode)
            self.total_tokens = (
                getattr(state, "total_tokens", self.total_tokens) or self.total_tokens
            )
            if not self._turn_rendered:
                msgs = [m for m in getattr(state, "messages", []) if m.get("role") == "assistant"]
                if msgs:
                    self._append_markdown(msgs[-1].get("content", ""))
            if getattr(state, "error", None):
                self._error(str(state.error))
        except asyncio.CancelledError:
            self._note("Interrupted.")
            raise
        except Exception as exc:  # pragma: no cover
            self._error(f"Execution failed: {exc}")
        finally:
            self._busy = False
            self._current_assistant = None
            self._assistant_text = ""
            self._stop_spinner()
            self.total_tokens += self.live_tokens
            elapsed = time.monotonic() - start
            self.update_hint(right=f"{elapsed:.1f}s · {self.model_name} · {self.mode}")

    # -- commands & shell ---------------------------------------------------
    def _handle_command(self, text: str) -> None:
        parts = text[1:].split()
        cmd = parts[0].lower() if parts else ""
        arg = parts[1] if len(parts) > 1 else ""
        if cmd in ("help", "h", "?"):
            self.action_help()
        elif cmd == "mode":
            if arg in MODES:
                self.mode = arg
                self._refresh_welcome()
                self.update_hint()
                self._note(f"Mode → {arg}")
            else:
                self._note(f"Modes: {', '.join(MODES)}")
        elif cmd == "model":
            if arg in PROVIDERS:
                if self._busy:
                    self._note("Cannot switch model while a task is running.")
                    return
                self._note(f"Switching provider → {arg}…")
                self._init_agent(provider=arg)
            elif arg:
                self._note(f"Unknown provider '{arg}'. Options: {', '.join(PROVIDERS)}")
            else:
                self._note(f"Current model: {self.model_name}")
        elif cmd == "workspace":
            if arg:
                self.workspace = arg
                self._refresh_welcome()
                self._note(f"Workspace → {arg}")
            else:
                self._note(f"Workspace: {self.workspace}")
        elif cmd == "copy":
            if arg == "all":
                self._copy_text("\n\n".join(self.transcript), "full transcript")
            else:
                self.action_copy_last()
        elif cmd == "clear":
            self.action_clear()
        elif cmd in ("quit", "exit", "q"):
            self.exit()
        else:
            self._note(f"Unknown command: /{cmd}. Press ? for shortcuts.")

    @work(exclusive=False, thread=True)
    def _run_shell(self, command: str) -> None:
        if not command:
            return
        self.call_from_thread(self._append, f"⏺ bash([italic]{command}[/])", "tool")
        import subprocess  # nosec B404 - explicit shell passthrough is a TUI feature

        try:
            proc = subprocess.run(  # nosec B602 - user-invoked passthrough
                command, shell=True, capture_output=True, text=True, timeout=60
            )
            out = ((proc.stdout or "") + (proc.stderr or "")).strip() or f"(exit {proc.returncode})"
            lines = out.splitlines()
            shown = "\n".join(lines[:20])
            if len(lines) > 20:
                shown += f"\n  [+{len(lines) - 20} more lines]"
            self.call_from_thread(self._append, "⎿  " + shown.replace("\n", "\n   "), "result")
        except Exception as exc:
            self.call_from_thread(self._error, f"shell: {exc}")

    # -- actions ------------------------------------------------------------
    def action_clear(self) -> None:
        conv = self.query_one("#conversation", VerticalScroll)
        conv.remove_children()
        conv.mount(Static(self._welcome_text(), id="welcome"))
        self._note("Cleared.")

    def action_cycle_mode(self) -> None:
        self.mode = MODES[(MODES.index(self.mode) + 1) % len(MODES)]
        self._refresh_welcome()
        self.update_hint()
        self._note(f"Mode → {self.mode}")

    def action_help(self) -> None:
        if not isinstance(self.screen, HelpScreen):
            self.push_screen(HelpScreen())

    @on(Input.Changed, "#command-input")
    def _on_changed(self, event: Input.Changed) -> None:
        # Claude Code behavior: a lone `?` opens the shortcuts panel.
        if event.value == "?":
            event.input.value = ""
            self.action_help()

    def action_interrupt_or_clear(self) -> None:
        if self._busy:
            self.workers.cancel_all()
            self._note("Interrupting…")
            return
        inp = self.query_one("#command-input", Input)
        if inp.value:
            inp.value = ""

    def action_copy_last(self) -> None:
        if not self.last_assistant_text:
            self._note("Nothing to copy yet — run a request first.")
            return
        self._copy_text(self.last_assistant_text, "last response")

    def _copy_text(self, text: str, label: str) -> None:
        if not text:
            self._note("Nothing to copy.")
            return
        try:
            self.copy_to_clipboard(text)
            self._note(f"Copied {label} ({len(text)} chars) to clipboard.")
        except Exception as exc:  # pragma: no cover
            self._error(f"Copy failed: {exc}")

    # -- spinner ------------------------------------------------------------
    def _start_spinner(self) -> None:
        self._spin = 0
        self._spin_word = random.choice(SPIN_WORDS)
        self._start_time = time.monotonic()
        self.query_one("#thinking", Static).add_class("active")
        if self._spin_timer is None:
            self._spin_timer = self.set_interval(0.12, self._tick_spinner)

    def _tick_spinner(self) -> None:
        self._spin = (self._spin + 1) % len(SPIN_SYMBOLS)
        if self._spin % len(SPIN_SYMBOLS) == 0:
            self._spin_word = random.choice(SPIN_WORDS)
        elapsed = int(time.monotonic() - self._start_time)
        sym = SPIN_SYMBOLS[self._spin]
        tok = f"↑ {self.live_tokens} tokens" if self.live_tokens else "working"
        self.query_one("#thinking", Static).update(
            f"{sym} [{ACCENT}]{self._spin_word}…[/] "
            f"[{DIM}]({elapsed}s · {tok} · esc to interrupt)[/]"
        )

    def _stop_spinner(self) -> None:
        if self._spin_timer is not None:
            self._spin_timer.stop()
            self._spin_timer = None
        th = self.query_one("#thinking", Static)
        th.remove_class("active")
        th.update("")

    # -- rendering ----------------------------------------------------------
    @staticmethod
    def _md(text: str) -> RichMarkdown:
        return RichMarkdown(text)

    def _append(self, text: str, css: str) -> None:
        self.query_one("#conversation", VerticalScroll).mount(Static(text, classes=f"block {css}"))
        self.transcript.append(text)
        self._scroll()

    def _append_markdown(self, text: str) -> None:
        self.query_one("#conversation", VerticalScroll).mount(
            Static(self._md(text), classes="block assistant")
        )
        self.transcript.append(text)
        self.last_assistant_text = text
        self._scroll()

    def _start_assistant(self) -> None:
        self._assistant_text = ""
        self._current_assistant = Static("", classes="block assistant")
        self.query_one("#conversation", VerticalScroll).mount(self._current_assistant)
        self._scroll()

    def _scroll(self) -> None:
        try:
            self.query_one("#conversation", VerticalScroll).scroll_end(animate=False)
        except Exception:  # pragma: no cover
            pass

    def _user(self, text: str) -> None:
        self._append(f"> {text}", "user")

    def _note(self, text: str) -> None:
        self._append(text, "note")

    def _error(self, text: str) -> None:
        self._append(f"✗ {text}", "err")

    def _refresh_welcome(self) -> None:
        try:
            self.query_one("#welcome", Static).update(self._welcome_text())
        except Exception:  # pragma: no cover - welcome may be cleared
            pass

    def update_hint(self, right: str | None = None) -> None:
        self.query_one("#hint-left", Static).update(
            f"[{MUTED}]? shortcuts · / commands · ! bash[/]"
        )
        self.query_one("#hint-right", Static).update(
            f"[{MUTED}]{right or f'{self.model_name} · {self.mode}'}[/]"
        )

    # -- helpers ------------------------------------------------------------
    @staticmethod
    def _extract_result(res: Any) -> tuple[str, str | None]:
        if res is None:
            return "", None
        tr = getattr(res, "tool_result", None)
        if tr is not None:
            return (getattr(tr, "stdout", "") or ""), getattr(tr, "error", None)
        if isinstance(res, dict):
            inner = res.get("tool_result", {}) or {}
            if isinstance(inner, dict):
                return (inner.get("stdout") or ""), inner.get("error")
            return (res.get("stdout") or ""), res.get("error")
        return str(res), None

    @staticmethod
    def _finding_title(finding: Any) -> str:
        if finding is None:
            return "(untitled)"
        if isinstance(finding, dict):
            return str(finding.get("title") or finding.get("type") or "finding")
        return str(getattr(finding, "title", None) or getattr(finding, "type", None) or "finding")


def main() -> int:
    """Console-script entry point (``redforge-tui``)."""
    return RedForgeTUI().run() or 0


if __name__ == "__main__":
    RedForgeTUI().run()

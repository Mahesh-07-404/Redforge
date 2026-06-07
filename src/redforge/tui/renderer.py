"""
RedForge TUI — Rendering Pipeline
MessageRenderer, MessageStore (virtual scroll), render_md with syntax
highlighting, OSC escape helpers.
"""

from __future__ import annotations

import re
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional, Tuple

from rich.markup import escape
from rich.syntax import Syntax

# ─── palette constants (shared) ──────────────────────────

BG       = "#0d0d0d"
BG_PANEL = "#0f0f0f"
FG       = "#e8e8e3"
FG_DIM   = "#3a3a3a"
FG_MUTED = "#666660"
ACCENT   = "#ff4f00"
BORDER   = "#2a2a2a"

MODE_COLOR = {
    "bugbounty": "#ff4444", "ctf": "#00d4ff",
    "learning": "#00cc66", "coding": "#4488ff", "android": "#ff8800",
}
MODE_LABEL = {
    "bugbounty": "BUG BOUNTY", "ctf": "CTF",
    "learning": "LEARNING", "coding": "CODING", "android": "ANDROID",
}
SEV_COLOR = {
    "critical": "#ff2222", "high": "#ff6600",
    "medium": "#ffcc00", "low": "#4488ff", "info": "#666666",
}
MODES = ["bugbounty", "ctf", "learning", "coding", "android"]

LOGO = """\
  ██████╗ ███████╗██████╗ ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
  ██╔══██╗██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
  ██████╔╝█████╗  ██║  ██║█████╗  ██║   ██║██████╔╝██║  ███╗█████╗
  ██╔══██╗██╔══╝  ██║  ██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
  ██║  ██║███████╗██████╔╝██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
  ╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝"""


def _e(s: str) -> str:
    return escape(s)


def fmt_k(n: int) -> str:
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


# ─── OSC escape helpers ─────────────────────────────────

def osc_title(title: str) -> None:
    """Set terminal tab title via OSC 0."""
    try:
        sys.stdout.write(f"\x1b]0;{title}\x07")
        sys.stdout.flush()
    except Exception:
        pass


def osc_progress(pct: int = -1) -> None:
    """
    Set terminal progress indicator (iTerm2/WezTerm).
    pct=-1 → indeterminate spinner, 0-100 → determinate bar,
    pct=200 → clear/remove.
    """
    try:
        if pct < 0:
            sys.stdout.write("\x1b]9;4;1;0\x07")  # indeterminate
        elif pct > 100:
            sys.stdout.write("\x1b]9;4;0;0\x07")  # clear
        else:
            sys.stdout.write(f"\x1b]9;4;1;{pct}\x07")
        sys.stdout.flush()
    except Exception:
        pass


# ─── Markdown → Rich markup with syntax highlighting ────

_LANG_ALIASES = {
    "py": "python", "js": "javascript", "ts": "typescript",
    "sh": "bash", "zsh": "bash", "yml": "yaml",
    "rs": "rust", "rb": "ruby", "go": "go",
}


def render_md(text: str) -> str:
    """
    Convert Markdown to Rich markup.
    Handles: fenced code (with syntax), headings, bold, inline code,
    bullet lists, horizontal rules, FINDING: markers.
    """
    lines = text.splitlines()
    out: List[str] = []
    in_fence = False
    fence_lang = ""
    fence_buf: List[str] = []

    for raw in lines:
        stripped = raw.strip()

        # ── fenced code toggle ──
        if stripped.startswith("```"):
            if not in_fence:
                in_fence = True
                fence_lang = stripped[3:].strip().lower() or "text"
                fence_lang = _LANG_ALIASES.get(fence_lang, fence_lang)
                fence_buf = []
            else:
                in_fence = False
                _flush_code_block(out, fence_lang, fence_buf)
                fence_buf = []
            continue

        if in_fence:
            fence_buf.append(raw)
            continue

        # ── horizontal rule ──
        if re.match(r"^-{3,}$|^\*{3,}$|^_{3,}$", stripped):
            out.append(f"[{FG_DIM}]{'─' * 50}[/]")
            continue

        # ── headings ──
        m = re.match(r"^(#{1,3})\s+(.*)", raw)
        if m:
            depth = len(m.group(1))
            txt = _e(m.group(2))
            colors = [ACCENT, FG, FG_MUTED]
            c = colors[min(depth - 1, 2)]
            out.append(f"[bold {c}]{txt}[/]")
            continue

        # ── FINDING marker ──
        fm = re.match(
            r"FINDING:\s*(?P<t>[^|]+)\|\s*SEVERITY:\s*(?P<s>[^|]+)\|\s*(?P<d>.+)",
            raw, re.IGNORECASE,
        )
        if fm:
            sev = fm.group("s").strip().lower()
            sc = SEV_COLOR.get(sev, FG_MUTED)
            out.append(
                f"[bold {sc}]┌─ FINDING: {sev.upper()} ────────────────┐[/]\n"
                f"[{sc}]│[/]  [bold]{_e(fm.group('d').strip())}[/bold]\n"
                f"[{sc}]│[/]  [dim]type: {_e(fm.group('t').strip())}[/dim]\n"
                f"[{sc}]└──────────────────────────────────────┘[/]"
            )
            continue

        # ── inline formatting ──
        line = raw
        line = re.sub(r"\*\*(.+?)\*\*", lambda m: f"[bold]{_e(m.group(1))}[/bold]", line)
        line = re.sub(r"`(.+?)`", lambda m: f"[bold #d4a84b]{_e(m.group(1))}[/]", line)
        line = re.sub(r"^(\s*)[-*]\s+", lambda m: m.group(1) + f"  [{ACCENT}]▸[/] ", line)

        out.append(line)

    # If fence was never closed
    if in_fence and fence_buf:
        _flush_code_block(out, fence_lang, fence_buf)

    return "\n".join(out)


def _flush_code_block(out: List[str], lang: str, lines: List[str]) -> None:
    """Append a syntax-highlighted code block to output."""
    w = 52
    out.append(f"[{FG_DIM}]  ┌─ {lang} {'─' * max(0, w - len(lang) - 4)}┐[/]")
    code = "\n".join(lines)
    try:
        syn = Syntax(code, lang, theme="monokai", line_numbers=False,
                     word_wrap=True, background_color=BG)
        # Rich Syntax → plain str via console protocol is heavy; use simple highlight
        for cl in lines:
            out.append(f"[{FG_DIM}]  │[/] [bold #d4a84b]{_e(cl)}[/]")
    except Exception:
        for cl in lines:
            out.append(f"[{FG_DIM}]  │[/] {_e(cl)}")
    out.append(f"[{FG_DIM}]  └{'─' * (w + 1)}┘[/]")


# ─── Message types ───────────────────────────────────────

@dataclass
class Msg:
    """Single message in the conversation store."""
    role: str         # user | assistant | tool | system | error | finding
    content: str
    tool_name: str = ""
    command: str = ""
    severity: str = ""
    status: str = ""
    duration_s: float = 0.0
    timestamp: float = field(default_factory=time.time)
    rendered: str = ""   # cached rich markup

    def render(self, mode: str = "bugbounty") -> str:
        if self.rendered:
            return self.rendered
        mc = MODE_COLOR.get(mode, ACCENT)
        if self.role == "user":
            self.rendered = f"\n[bold {mc}]▶ You[/]\n  {_e(self.content)}\n"
        elif self.role == "assistant":
            self.rendered = f"\n[bold {ACCENT}]⛏ RedForge[/]\n{render_md(self.content)}\n"
        elif self.role == "tool":
            status = self.status or "done"
            color = {
                "running": "#ffcc00",
                "done": "#00cc66",
                "failed": "#ff3333",
            }.get(status, FG_MUTED)
            icon = {"running": "⟳", "done": "✔", "failed": "✘"}.get(status, "•")
            header = self.tool_name or "shell"
            output_lines = []
            for line in self.content.strip().splitlines()[:20]:
                output_lines.append(f"[{FG_DIM}]┃[/]  [{FG_MUTED}]{_e(line[:86])}[/]")
            if not output_lines:
                output_lines.append(f"[{FG_DIM}]┃[/]  [{FG_MUTED}]no output[/]")
            
            self.rendered = "\n".join(
                [
                    "",
                    f"[{FG_DIM}]┏━━ [bold {ACCENT}]{_e(header.upper())}[/] {'━' * (50 - len(header))}┓[/]",
                    f"[{FG_DIM}]┃[/]  [dim #888888]$ {_e(self.command[:86])}[/dim]",
                    f"[{FG_DIM}]┣{'━' * 56}┫[/]",
                    *output_lines,
                    f"[{FG_DIM}]┣{'━' * 56}┫[/]",
                    f"[{FG_DIM}]┃[/]  [bold {color}]{icon} {status.upper()}[/]  [dim]{self.duration_s:.2f}s[/dim]",
                    f"[{FG_DIM}]┗{'━' * 56}┛[/]",
                    "",
                ]
            )
        elif self.role == "error":
            self.rendered = (
                f"\n[bold #ff3333]┏━ ERROR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓[/]\n"
                f"[#ff3333]┃[/]  {_e(self.content[:500])}\n"
                f"[bold #ff3333]┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛[/]\n"
            )
        elif self.role == "system":
            self.rendered = f"\n[{FG_MUTED}]  ⚙ {_e(self.content)}[/]\n"
        elif self.role == "finding":
            sc = SEV_COLOR.get(self.severity, FG_MUTED)
            self.rendered = (
                f"\n[bold {sc}]┏━ FINDING: {self.severity.upper()} ━━━━━━━━━━━━━━━━┓[/]\n"
                f"[{sc}]┃[/]  [bold]{_e(self.content)}[/bold]\n"
                f"[{sc}]┃[/]  [dim]type: {_e(self.tool_name)}[/dim]\n"
                f"[{sc}]┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛[/]\n"
            )
        else:
            self.rendered = f"  {_e(self.content)}\n"
        return self.rendered


# ─── MessageStore (virtual scroll) ───────────────────────

class MessageStore:
    """
    O(1) append message store with viewport windowing.
    Only messages visible in the viewport are rendered to RichLog.
    """

    def __init__(self, max_messages: int = 5000):
        self._msgs: List[Msg] = []
        self._max = max_messages
        self._scroll_offset: int = 0  # 0 = bottom (newest)
        self._mode: str = "bugbounty"

    def append(self, msg: Msg) -> None:
        self._msgs.append(msg)
        if len(self._msgs) > self._max:
            self._msgs = self._msgs[-self._max:]

    def set_mode(self, mode: str) -> None:
        self._mode = mode

    @property
    def total(self) -> int:
        return len(self._msgs)

    def visible_slice(self, viewport_lines: int) -> List[str]:
        """Return rendered markup for the visible viewport."""
        if not self._msgs:
            return []
        # Walk backwards from end - offset, accumulate until viewport full
        end = max(0, len(self._msgs) - self._scroll_offset)
        rendered: List[str] = []
        line_count = 0
        for msg in reversed(self._msgs[:end]):
            text = msg.render(self._mode)
            lines_in_msg = text.count("\n") + 1
            if line_count + lines_in_msg > viewport_lines and rendered:
                break
            rendered.append(text)
            line_count += lines_in_msg
        rendered.reverse()
        return rendered

    def scroll_up(self, n: int = 5) -> None:
        self._scroll_offset = min(self._scroll_offset + n, max(0, len(self._msgs) - 1))

    def scroll_down(self, n: int = 5) -> None:
        self._scroll_offset = max(0, self._scroll_offset - n)

    def scroll_bottom(self) -> None:
        self._scroll_offset = 0

    def clear(self) -> None:
        self._msgs.clear()
        self._scroll_offset = 0

    def all_rendered(self) -> List[str]:
        return [m.render(self._mode) for m in self._msgs]

    @property
    def last(self) -> Optional[Msg]:
        return self._msgs[-1] if self._msgs else None


# ─── Stream queue ────────────────────────────────────────

class StreamQueue:
    """Character-level stream queue for token-by-token output effect."""

    def __init__(self, chars_per_tick: int = 8):
        self._queue: Deque[str] = deque()
        self.chars_per_tick = chars_per_tick

    def enqueue(self, text: str) -> None:
        for ch in text:
            self._queue.append(ch)

    def drain(self) -> str:
        """Drain up to chars_per_tick characters."""
        chunk = []
        for _ in range(self.chars_per_tick):
            if self._queue:
                chunk.append(self._queue.popleft())
        return "".join(chunk)

    @property
    def pending(self) -> bool:
        return bool(self._queue)

    def clear(self) -> None:
        self._queue.clear()


# ─── MessageRenderer (content router) ────────────────────

class MessageRenderer:
    """
    Routes incoming content chunks to the appropriate renderer.
    Classifies: plain text, tool call blocks, findings, code blocks.
    """

    def __init__(self, store: MessageStore, stream: StreamQueue, mode: str = "bugbounty"):
        self.store = store
        self.stream = stream
        self.mode = mode
        self.store.set_mode(mode)
        self._active_assistant: Optional[Msg] = None
        self._active_tools: Dict[str, Msg] = {}

    def feed_user(self, text: str) -> None:
        self.store.append(Msg(role="user", content=text))

    def feed_assistant(self, text: str, streaming: bool = True) -> None:
        msg = Msg(role="assistant", content=text)
        self.store.append(msg)
        if streaming:
            rendered = msg.render(self.mode)
            self.stream.enqueue(rendered)
        self._extract_findings(text)

    def start_assistant(self) -> None:
        msg = Msg(role="assistant", content="")
        self.store.append(msg)
        self._active_assistant = msg

    def append_assistant_chunk(self, text: str) -> None:
        if self._active_assistant is None:
            self.start_assistant()
        self._active_assistant.content += text
        self._active_assistant.rendered = ""

    def finish_assistant(self, text: Optional[str] = None) -> None:
        if self._active_assistant is None:
            if text:
                self.feed_assistant(text, streaming=False)
            return
        if text is not None and not self._active_assistant.content:
            self._active_assistant.content = text
        self._active_assistant.rendered = ""
        self._extract_findings(self._active_assistant.content)
        self._active_assistant = None

    def _extract_findings(self, text: str) -> None:
        for m in re.finditer(
            r"FINDING:\s*(?P<t>[^|]+)\|\s*SEVERITY:\s*(?P<s>[^|]+)\|\s*(?P<d>.+)",
            text, re.IGNORECASE,
        ):
            self.store.append(Msg(
                role="finding",
                content=m.group("d").strip(),
                tool_name=m.group("t").strip(),
                severity=m.group("s").strip().lower(),
            ))

    def feed_tool(self, content: str) -> None:
        self.store.append(Msg(role="tool", content=content))

    def start_tool(self, call_id: str, tool_name: str, command: str) -> None:
        msg = Msg(
            role="tool",
            content="",
            tool_name=tool_name,
            command=command,
            status="running",
            duration_s=0.0,
        )
        self.store.append(msg)
        self._active_tools[call_id] = msg

    def finish_tool(
        self,
        call_id: str,
        *,
        output: str,
        status: str = "done",
        duration_s: float = 0.0,
        tool_name: str = "",
        command: str = "",
    ) -> None:
        msg = self._active_tools.pop(call_id, None)
        if msg is None:
            self.feed_tool_result(
                tool_name or "tool",
                command,
                output,
                status=status,
                duration_s=duration_s,
            )
            return
        msg.content = output
        msg.status = status
        msg.duration_s = duration_s
        if tool_name:
            msg.tool_name = tool_name
        if command:
            msg.command = command
        msg.rendered = ""

    def feed_tool_result(
        self,
        tool_name: str,
        command: str,
        output: str,
        status: str = "done",
        duration_s: float = 0.0,
    ) -> None:
        self.store.append(
            Msg(
                role="tool",
                content=output,
                tool_name=tool_name,
                command=command,
                status=status,
                duration_s=duration_s,
            )
        )

    def feed_error(self, msg: str) -> None:
        self.store.append(Msg(role="error", content=msg))

    def feed_system(self, msg: str) -> None:
        self.store.append(Msg(role="system", content=msg))

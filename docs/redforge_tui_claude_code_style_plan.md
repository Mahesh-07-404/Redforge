# RedForge TUI - Claude Code-Style Implementation Plan

## Overview

Replace the existing basic TUI (`src/redforge/tui/textual_tui.py`, 327 lines) with a professional, Claude Code-inspired terminal UI. Clean, dark, keyboard-first, with intelligent streaming output.

- Tech Stack: Python + Textual
- File to Create: `src/redforge/tui/textual_tui.py` (~1200 lines)
- Estimated Phases: 9

## Target Layout

```text
┌─────────────────────────────────────────────────────────────────┐
│ ● RedForge  [BUG]  [model: ollama]  [SAFE]                     │
├──────────────┬──────────────────────────────────────────────────┤
│              │                                                   │
│  WORKSPACE   │   OUTPUT AREA (scrolling chat)                    │
│  ─────────── │                                                   │
│  ● Tools     │   > scan example.com                              │
│    ⏳ nmap   │                                                   │
│    ✓ ffuf   │   ╔══ tool: nmap ════════════════════╗           │
│    ✗ sqlmap │   ║ $ nmap -sV -p 80,443 target.com ║           │
│  ● Workspace │   ╚══════════════════════════════════╝           │
│    example   │                                                   │
│  ● Memory    │   ✓ Found: 22/tcp open                           │
│    3 hits    │                                                   │
│  ● History   │                                                   │
│    12 msgs   │                                                   │
├──────────────┴──────────────────────────────────────────────────┤
│  > _                                               [1.2k tokens] │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                    RedForge TUI App                          │
├──────────────────────────────────────────────────────────────┤
│  Component Tree:                                             │
│                                                              │
│  RedForgeTUI (App)                                           │
│  ├── SplashScreen (shown for 1s on startup)                  │
│  ├── HeaderBar (1 line, mode-colored)                        │
│  ├── ContentArea (Horizontal split)                          │
│  │   ├── Sidebar (collapsible, width: 24)                    │
│  │   │   ├── ToolsSection (status icons)                     │
│  │   │   ├── WorkspaceSection                                │
│  │   │   ├── MemorySection                                   │
│  │   │   └── HistorySection                                  │
│  │   └── OutputPanel (ScrollableContainer)                   │
│  │       ├── UserMessage                                     │
│  │       ├── ToolBlock (box-drawing)                         │
│  │       ├── AssistantMessage (streaming)                    │
│  │       └── ...                                             │
│  ├── InputBar (always focused, vim-style)                    │
│  └── StatusFooter (tokens, model, latency)                   │
│                                                              │
│  Agent Integration:                                          │
│  └── redforge.core.agent → Agent                             │
│      └── AgentState → subscribed for live updates            │
└──────────────────────────────────────────────────────────────┘
```

## Phase 1: Splash Screen

- Files: Inline in `textual_tui.py`
- Lines: ~60

Displays for 1 second on startup, then transitions to main layout.

```text
   ██████╗ ███████╗██████╗ ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
   ██╔══██╗██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
   ██████╔╝█████╗  ██║  ██║█████╗  ██║   ██║██████╔╝██║  ███╗█████╗
   ██╔══██╗██╔══╝  ██║  ██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
   ██║  ██║███████╗██████╔╝██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
   ╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
                 Autonomous Security Intelligence — v0.1
```

Implementation:

- Custom `Screen` class with `Timer`
- After 1 second, switch to main `Screen`
- Color: accent orange (`#ff4f00`)

## Phase 2: Header Bar

- Lines: ~80
- Widget: `Container` with `id="header"`

Content (1 line):

```text
● RedForge  [BUG]  [model: ollama/llama3.2]  [SAFE]
```

Elements:

| Element | Position | Color |
|---|---|---|
| Brand mark | Left | `#ff4f00` |
| `RedForge` | Left | `#ff4f00` bold |
| Mode badge | Center-left | Per mode |
| Model | Center | `#666` |
| Safety | Right | `#00ff88` (SAFE) or `#ff3333` (UNSAFE) |

Mode colors:

| Mode | Badge Text | Color |
|---|---|---|
| bugbounty | `[BUG]` | `#ff4f00` |
| ctf | `[CTF]` | `#00d4ff` |
| learning | `[LRN]` | `#00ff88` |
| coding | `[COD]` | `#0088ff` |
| android | `[AND]` | `#ff8800` |

## Phase 3: Collapsible Sidebar

- Lines: ~200
- Widget: `Vertical` with `id="sidebar"`
- Width: 24 chars
- Toggle: `Ctrl+B` (add/remove class `collapsed`)

Sections:

```text
  WORKSPACE
  ────────────
  target: example.com
  workspace: /home/...
  TOOLS
  ────────────
  ⏳ nmap
  ✓ ffuf
  ✗ sqlmap
  MEMORY
  ────────────
  3 recent hits
  retrieved: port_scan.md
  HISTORY
  ────────────
  12 messages
  3 tool calls
```

When collapsed:

- `width = 0`
- `display: none`

## Phase 4: Output Panel

- Lines: ~250
- Widget: `ScrollableContainer` with `id="output"`

Message types:

| Role | Prefix | Color |
|---|---|---|
| user | `>` | `#ff4f00` bold |
| assistant | (none) | `#e8e8e3` |
| system | `●` | `#666` dim |
| tool | `[tool: name]` | `#888` |
| error | `✗` | `#ff3333` |

Streaming effect:

```python
async def stream_text(self, content: str, widget: Static):
    """Stream text token-by-token"""
    for i in range(0, len(content), 4):  # 4-char chunks
        widget.update(content[:i + 4])
        await asyncio.sleep(0.02)  # 20ms per chunk
```

## Phase 5: Tool Call Blocks

- Lines: ~80
- Widget: `Static` with box-drawing characters

Format:

```text
╔══ tool: nmap ════════════════════════╗
║  $ nmap -sV -p 80,443 target.com     ║
╚══════════════════════════════════════╝
```

CSS:

```css
.tool-block {
    color: #888;
    margin: 1 2;
}
.tool-block-header {
    color: #ff4f00;
}
```

## Phase 6: Vim-Style Input Bar

- Lines: ~100
- Widget: `Input` with `id="command-input"`

Behaviors:

- Always focused (auto focus on submit)
- `/help`, `/mode`, `/clear`, `/model` → slash commands
- `!ls`, `!nmap` → shell passthrough
- `Tab` → autocomplete mode/tool names
- `Escape` → clear input / cancel
- `↑↓` → scroll history when input empty

Input states:

| First Char | Mode |
|---|---|
| (none) | Normal message to agent |
| `/` | Command mode |
| `!` | Shell passthrough |

## Phase 7: Keyboard Shortcuts

- Lines: ~40
- Bound via `BINDINGS` class variable

| Shortcut | Action | Description |
|---|---|---|
| `Ctrl+L` | `action_clear` | Clear output panel |
| `Ctrl+B` | `action_toggle_sidebar` | Show/hide sidebar |
| `Ctrl+M` | `action_cycle_mode` | Next mode |
| `Ctrl+K` | `action_kill_task` | Interrupt agent |
| `Escape` | `action_cancel` | Clear input / cancel |
| `↑` | message history | Scroll when input empty |
| `↓` | message history | Scroll when input empty |

## Phase 8: Slash Commands

- Lines: ~100
- Handled in `on_input_submit`

| Command | Action |
|---|---|
| `/help` | Show keyboard shortcuts overlay |
| `/mode bugbounty` | Switch to bugbounty mode |
| `/mode ctf` | Switch to CTF mode |
| `/mode learning` | Switch to learning mode |
| `/mode coding` | Switch to coding mode |
| `/mode android` | Switch to android mode |
| `/model ollama` | Switch to Ollama |
| `/model openai` | Switch to OpenAI |
| `/model gemini` | Switch to Gemini |
| `/clear` | Clear output panel |
| `/workspace /path` | Set workspace path |

## Phase 9: Agent Integration

- Lines: ~200
- Imports: `from redforge.core.agent import Agent, AgentState`

Integration pattern:

```python
# TUI holds agent instance
self.agent = Agent()

# Forward input to agent
async def process_input(self, user_input: str):
    # Show streaming output
    result = await self.agent.run(user_input)

    # Subscribe to events
    self.agent.on("tool_start", self.on_tool_start)
    self.agent.on("tool_end", self.on_tool_end)
    self.agent.on("token", self.on_token)
    self.agent.on("error", self.on_error)
```

Event handlers:

| Event | Action |
|---|---|
| `tool_start` | Render tool block header with `⏳` |
| `tool_end` | Update icon to `✓` or `✗` |
| `token` | Append to streaming `Static` |
| `error` | Render red bordered error block |

Sidebar updates:

```python
def update_sidebar_from_state(self):
    state = self.agent.state
    self.update_tools(state.tools_used)
    self.update_token_count(state.total_tokens)
    self.update_findings(state.findings)
```

## Color Palette Summary

- Background: `#0d0d0d`
- Surface: `#1a1a1a`
- Text: `#e8e8e3`
- Text Dim: `#666666`
- Accent: `#ff4f00`
- Border: `#3a3a3a`
- Mode - bugbounty: `#ff4f00`
- Mode - ctf: `#00d4ff`
- Mode - learning: `#00ff88`
- Mode - coding: `#0088ff`
- Mode - android: `#ff8800`
- Success: `#00ff88`
- Error: `#ff3333`
- Warning: `#ffaa00`

## Unicode Symbols

| Symbol | Meaning |
|---|---|
| `●` | Status indicator |
| `▸` | Active selection |
| `✓` | Success |
| `✗` | Failure |
| `⏳` | In progress |
| `─ │ ╔ ═ ╗ ║ ╚ ╝` | Box-drawing for tool blocks |

## File Structure (Final)

```text
src/redforge/tui/
├── __init__.py
├── app.py
├── screens.py
└── textual_tui.py
```

## Dependencies

Already in `pyproject.toml`:

- `textual`
- `rich`
- `pygments`

## Test Verification

```bash
cd /home/mahesh/RedForge
python3 -m pytest tests/ -q
```

Expected: `29 passed`

## Launch Commands

```bash
cd /home/mahesh/RedForge
python3 -m redforge.tui.textual_tui
python3 -c "from redforge.tui import launch_textual; launch_textual()"
```

## Implementation Order

1. Phase 1: Splash Screen
2. Phase 2 + 3: Header + Sidebar
3. Phase 4 + 5: Output + Tool Blocks
4. Phase 6 + 7: Input + Shortcuts
5. Phase 8: Slash Commands
6. Phase 9: Agent Integration
7. Final: Visual polish + testing

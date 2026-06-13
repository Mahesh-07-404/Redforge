# RedForge

**Autonomous CLI-based Penetration Testing AI Agent**

An intelligent security testing framework with 5 operational modes, 128+ specialized skills, and autonomous capability.

## Features

### Operational Modes
- **Bug Bounty** - Automated vulnerability hunting
- **CTF** - Capture The Flag competition assistant
- **Learning** - Security skill development
- **Coding** - Secure coding practice
- **Android** - Mobile application testing

### Core Capabilities
- **128+ Skill Files** - Dynamic skill-based guidance
- **LangGraph Agent** - Hybrid goal/knowledge-based reasoning
- **Workspace Memory** - RAG-powered context retention
- **Tool Auto-Install** - Missing tool detection and installation
- **Safety Engine** - Scope verification and ethical boundaries
- **TUI Interface** - Keyboard-first Textual terminal UI with a fuzzy command palette

### Supported Platforms
- Kali Linux, Debian, Ubuntu, Arch, Fedora
- macOS, Windows (WSL)

## Installation

```bash
# Clone repository
git clone https://github.com/redforge/redforge.git
cd redforge

# Install
pip install -e .

# Configure
cp config.yaml.example config.yaml
# Edit config.yaml with your LLM API keys

# Run
redforge --help
```

## Quick Start

```bash
# Interactive CLI
redforge

# Specific mode
redforge --mode bugbounty

# With target
redforge --mode bugbounty --target example.com

# TUI interface
redforge tui

# Check system health
redforge doctor
```

## Configuration

### LLM Provider (config.yaml)
```yaml
llm:
  provider: gemini  # or: openai, anthropic, groq, ollama
  model: gemini-3.5-flash
  api_key: ${GEMINI_API_KEY}  # hosted providers also read standard env vars
  base_url: http://localhost:11434  # for Ollama
```

### Safety Settings
```yaml
safety:
  level: warn  # off, warn, strict
  scope:
    domains:
      - example.com
    ip_ranges:
      - 192.168.1.0/24
```

## Usage

### TUI Command Palette

Run `redforge tui`, then type `/` to open the command palette instantly. The
palette is populated from the command registry, so valid dynamically registered
commands appear automatically.

Each entry displays its command and description:

```text
/help       Show all available commands
/mode       Change active mode
/target     Set scan target
/session    Manage sessions
/report     Generate findings report
```

Type part of a command to filter it. Matching is fuzzy, so `/mo` finds `/mode`
and `/mde` can also match `/mode`.

| Key | Action |
|-----|--------|
| `Up` / `Down` | Move the highlighted selection |
| `Tab` / `Shift+Tab` | Move forward or backward |
| `Enter` | Insert the highlighted command into the input |
| `Escape` | Close the palette without changing the current input |

Selecting a command does not execute it. For example, selecting `/mode` inserts
it into the editor. You can extend it to `/mode bugbounty`, then press `Enter`
to execute.

Command execution failures are shown in the TUI without terminating RedForge:

```text
Command Failed
Reason: <error details>
Suggested Fix: <recovery guidance>
```

### CLI Commands
```
redforge> help

Commands:
  mode [mode]     - Set or show current mode
  target [target] - Set target for testing
  scan            - Run vulnerability scan
  recon           - Run reconnaissance
  report          - Generate findings report
  exit            - Exit RedForge

Modes:
  bugbounty - Bug bounty hunting
  ctf       - CTF competition
  learning  - Skill development
  coding    - Secure coding
  android   - Mobile testing
```

### Mode-Specific Features

#### Bug Bounty Mode
- Reconnaissance automation
- Vulnerability scanning
- CVE generation
- Report generation (HackerOne, Bugcrowd formats)

#### CTF Mode
- Challenge categorization
- Flag validation
- Score tracking
- Writeup generation

#### Learning Mode
- Topic-based learning paths
- Progress tracking
- Exercise generation

## Architecture

```
RedForge/
├── src/redforge/
│   ├── core/          # Agent engine, LangGraph integration
│   ├── llm/           # LLM provider integrations
│   ├── memory/        # Vector storage, RAG
│   ├── modes/         # Mode implementations
│   ├── safety/        # Safety engine
│   ├── tools/         # Tool management
│   ├── platforms/     # Bug bounty platform integration
│   ├── tui/           # Terminal UI
│   └── web/           # Web dashboard API
├── skills/            # 128+ skill files
├── workspaces/         # Persistent workspace storage
└── tests/             # Test suite
```

## Skills Framework

Skills are organized by category and dynamically loaded based on context:

```
skills/
├── SYSTEM/            # Core agent skills
├── AUTONOMY/         # Autonomy control skills
├── MODES/
│   ├── BUGBOUNTY/    # Bug bounty hunting skills
│   ├── CTF/          # CTF competition skills
│   ├── LEARNING/     # Learning resources
│   ├── CODING/       # Secure coding
│   └── ANDROID/      # Mobile testing
├── TOOLS/            # Tool usage guides
├── SAFETY/           # Safety guidelines
└── LLM/              # LLM optimization
```

## Development

### Setup Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linting
ruff check src/
```

### Adding New Skills
Create a new `.md` file in the appropriate category:
```markdown
# Category Skill: Feature Name

## Purpose
Brief description of the skill.

## Framework
Key concepts and approaches.

## Examples
Usage examples and patterns.
```

### Registering TUI Commands

Use the command registry instead of adding commands directly to the palette:

```python
from redforge.tui.palette import CommandRegistry

CommandRegistry.register(
    "exploit_active",
    "Trigger the active exploitation workflow",
)
```

Command names and descriptions are validated before display. Invalid or
duplicate entries are excluded from the palette.

### Command Palette Tests

```bash
# Focused palette tests
pytest -q tests/test_palette.py

# Complete test suite
pytest -q
```

The focused suite covers opening, closing, fuzzy filtering, keyboard navigation,
selection, input preservation, dynamic registration, and execution only after a
separate `Enter` press.

## Autonomy Levels

| Level | Description |
|-------|-------------|
| MANUAL | Step-by-step approval (Safe Default) |
| PARTIAL | Auto safe, confirm destructive |
| FULL | Full autonomous (Requires consent) |

## License

MIT License - See [LICENSE](LICENSE)

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

## Roadmap

- [x] Core agent engine
- [x] LangGraph integration
- [x] 128+ skill files
- [x] Tool auto-install
- [x] Safety engine
- [x] Mode implementations
- [x] Bug bounty platform integration
- [x] Web dashboard
- [ ] Mobile TUI app
- [ ] Plugin system
- [ ] Team collaboration features

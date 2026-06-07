# Session Management

## Session Lifecycle

### 1. Session Creation
```
User Input → Workspace Selection → Context Loading → Agent Initialization
```

### 2. Active Session
```
User Input → Thought Process → Tool Execution → Response → Memory Update
```

### 3. Session Termination
```
Explicit Exit or Timeout → State Save → Memory Commit → Cleanup
```

## Session States

| State | Description |
|-------|-------------|
| INITIALIZING | Setting up context and tools |
| READY | Awaiting user input |
| PROCESSING | Handling request |
| WAITING_CONFIRMATION | Pending user approval |
| ERROR | Recovery mode |
| COMPLETED | Task finished |

## Session Persistence

### Auto-save
- Enabled by default
- Saves every 60 seconds
- Saves on significant actions
- Saves on exit

### Manual Save
```bash
# Not implemented yet - reserved for future
redforge session save <session_id>
```

### Session Recovery
- Detect interrupted sessions
- Offer recovery on restart
- Merge partial findings

## Session Commands

```bash
# List sessions
redforge workspaces

# Create new workspace
redforge create-workspace <name>

# Switch workspace
# (via CLI or TUI)
```

## Session Context

Each session maintains:
- Mode (bugbounty, ctf, learning, coding, android)
- Autonomy level
- Target scope
- Findings
- Tool outputs
- Chat history

## Timeout Handling

- Idle timeout: 30 minutes
- Long operation warning: 5 minutes
- Forced save: On any interruption

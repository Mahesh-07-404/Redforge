# Memory Usage Guide

## Workspace Memory

RedForge maintains persistent memory across sessions using a workspace-based system.

### Core Concepts

1. **Workspaces**: Isolated environments for different projects
2. **Sessions**: Individual interaction instances within a workspace
3. **Findings**: Documented vulnerabilities or results
4. **Notes**: User annotations and observations

### Memory Types

#### Short-term Memory
- Current conversation context
- Active task state
- Recent tool outputs
- LLM context window

#### Long-term Memory
- Workspace history
- Past findings
- User preferences
- Learned patterns

### RAG Integration

RedForge uses Retrieval-Augmented Generation for context-aware responses:

```
Query → Vector Search → Relevant Context → LLM → Response
```

### Best Practices

1. **Initialize Workspace**: Start with clear objectives
2. **Save Findings**: Document discoveries immediately
3. **Review Context**: Check memory before starting new tasks
4. **Clean Up**: Remove outdated or irrelevant entries

### Memory Commands

```bash
redforge memory -w <workspace>  # View memory stats
redforge search "query"         # Search memory
redforge workspaces             # List workspaces
```

### Context Injection

The agent automatically retrieves relevant context:
- Previous findings on similar targets
- User preferences and settings
- Mode-specific knowledge
- Tool usage history

### Memory Limits

- Vector store: Unlimited entries (disk-dependent)
- Context window: Provider-dependent (typically 8K-128K tokens)
- Session history: Last 100 messages in context

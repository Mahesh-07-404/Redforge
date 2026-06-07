# Context Injection

## Context Types

### 1. System Context
- Agent instructions
- Safety guidelines
- Capability limits

### 2. Workspace Context
- Current target information
- Scope definition
- Previous findings
- Session history

### 3. Task Context
- Current objective
- Tool outputs
- Intermediate results

### 4. Knowledge Context
- Retrieved documents
- Skill references
- Relevant examples

## Injection Methods

### Prepend Context
```python
context = load_context()
prompt = f"{context}\n\nUser Query: {query}"
```

### Insert Context
```python
prompt = f"""Task: {task}

Relevant Information:
{retrieved_context}

Previous Results:
{previous_results}

Now execute the task:
"""
```

### Multi-turn Context
```python
# Build conversation
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "system", "content": context},
    {"role": "user", "content": query}
]
```

## Context Management

### Truncation
```python
# If context too long
if len(tokens) > max_tokens:
    context = summarize(context, max_tokens)
```

### Priority
```python
# What to include first
priority_order = [
    "safety_instructions",
    "current_task",
    "critical_findings",
    "workspace_info"
]
```

### Refresh
```python
# Update stale context
if context_age > refresh_interval:
    updated_context = refresh_context(old_context)
```

## Template Context

```python
context_template = """
=== WORKSPACE: {workspace_name} ===
Target: {target}
Scope: {scope}
Mode: {mode}

=== RECENT FINDINGS ===
{findings_summary}

=== SESSION HISTORY ===
{history_summary}

=== CURRENT TASK ===
{task_description}
"""
```

## Best Practices

1. **Keep concise**: Only essential context
2. **Prioritize**: Most important first
3. **Validate**: Ensure context is accurate
4. **Refresh**: Update stale information
5. **Token budget**: Reserve space for response

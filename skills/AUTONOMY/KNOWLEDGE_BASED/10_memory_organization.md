# Memory Organization

## Memory Structure

### Hierarchical Memory
```
Global Knowledge
├── Security Concepts
│   ├── Web Vulnerabilities
│   │   ├── SQL Injection
│   │   ├── XSS
│   │   └── CSRF
│   └── Network Security
│       ├── Scanning
│       └── Enumeration
├── Tools
│   ├── Reconnaissance
│   ├── Exploitation
│   └── Post-Exploitation
└── Techniques
    ├── Methodology
    └── Procedures
```

### Workspace Memory
```
Workspace: BugBounty-Example
├── Scope
│   ├── In-scope domains
│   └── Out-of-scope domains
├── Findings
│   ├── High severity
│   ├── Medium severity
│   └── Low severity
├── Sessions
│   ├── Recon notes
│   ├── Test results
│   └── Scripts
└── Artifacts
    ├── Screenshots
    └── PoC files
```

## Organization Principles

### 1. Categorization
```python
categories = [
    "vulnerability",
    "tool",
    "technique",
    "finding",
    "note"
]
```

### 2. Tagging
```python
tags = [
    "sql-injection",
    "owasp-top-10",
    "web",
    "database",
    "authentication"
]
```

### 3. Timestamping
```python
memory_entry = {
    "content": "...",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T12:00:00",
    "accessed_at": "2024-01-15T14:00:00"
}
```

## Retrieval Organization

### By Category
```python
get_memories(category="vulnerability")
```

### By Tag
```python
get_memories(tags=["sql-injection", "critical"])
```

### By Time
```python
get_memories(start_date="2024-01-01", end_date="2024-01-31")
```

### By Workspace
```python
get_memories(workspace_id="ws-123")
```

## Memory Maintenance

### Cleanup
- Remove duplicates
- Archive old entries
- Update stale information

### Indexing
```python
# Rebuild search index
for memory in memories:
    index.add(memory.embedding, memory.id)
```

## Best Practices

1. **Consistent naming**: Use standard formats
2. **Rich metadata**: Tags, dates, sources
3. **Regular cleanup**: Remove outdated info
4. **Proper categorization**: Easy retrieval
5. **Link related**: Connect related memories

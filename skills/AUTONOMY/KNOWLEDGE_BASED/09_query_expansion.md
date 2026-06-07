# Query Expansion

## Expansion Techniques

### 1. Synonym Expansion
```python
query = "SQL injection"
expanded = [
    "SQL injection",
    "SQLi",
    "database injection",
    "structured query language injection"
]
```

### 2. Related Term Expansion
```python
related = {
    "XSS": ["cross-site scripting", "javascript injection", "DOM XSS"],
    "CSRF": ["cross-site request forgery", "session riding"],
    "SSRF": ["server-side request forgery", "URL injection"]
}
```

### 3. Abbreviation Expansion
```python
abbrevs = {
    "SQLi": "SQL injection",
    "XSS": "cross site scripting",
    "RCE": "remote code execution",
    "LFI": "local file inclusion"
}
```

## Expansion Pipeline

```
Original Query
      ↓
Tokenize
      ↓
Expand Terms
      ↓
Add Related
      ↓
Construct Queries
      ↓
Execute Search
```

## Implementation

```python
def expand_query(query):
    tokens = tokenize(query)
    expanded = []
    
    for token in tokens:
        expanded.append(token)
        expanded.extend(get_synonyms(token))
        expanded.extend(get_related(token))
    
    # Unique terms
    unique = list(set(expanded))
    
    # Construct expanded queries
    queries = [
        " AND ".join(unique),  # All terms
        " OR ".join(unique),   # Any term
        query  # Original
    ]
    
    return queries
```

## Expansion Categories

### Technical Terms
- Vulnerability types
- Attack techniques
- Security tools

### Domain Terms
- Web security
- Network security
- Mobile security

### Contextual Terms
- Testing phases
- Assessment types
- Target types

## Best Practices

1. **Balance**: Don't over-expand
2. **Relevance**: Only related terms
3. **Deduplication**: Remove duplicates
4. **Quality**: Higher precision in search
5. **Iteration**: Refine based on results

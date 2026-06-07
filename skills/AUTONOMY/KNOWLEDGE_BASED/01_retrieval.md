# Knowledge Retrieval

## Retrieval Pipeline

```
Query → Parse → Search → Rank → Retrieve → Synthesize
```

## Query Types

### Factual Queries
"What is XSS?"
"How does SQL injection work?"

### Procedural Queries
"How do I test for SQL injection?"
"What are the steps for reconnaissance?"

### Comparative Queries
"nmap vs masscan?"
"SQLMap vs manual testing?"

## Retrieval Methods

### 1. Exact Match
```python
result = exact_match(query, knowledge_base)
```

### 2. Semantic Search
```python
results = semantic_search(
    query=query,
    documents=knowledge_base,
    top_k=5
)
```

### 3. Keyword Search
```python
results = keyword_search(
    query=query,
    documents=knowledge_base,
    operator="AND"
)
```

### 4. Hybrid Search
```python
results = hybrid_search(
    query=query,
    documents=knowledge_base,
    semantic_weight=0.7,
    keyword_weight=0.3
)
```

## Knowledge Sources

### Internal Sources
- Workspace memory
- Session history
- Findings database
- Skill files

### External Sources
- Documentation
- CVE databases
- OWASP guidelines
- Security blogs

## Retrieval Best Practices

1. **Clear Queries**: Specific questions get better results
2. **Filter Early**: Remove irrelevant results
3. **Rank by Relevance**: Most relevant first
4. **Deduplicate**: Remove duplicates
5. **Freshness**: Prefer recent information

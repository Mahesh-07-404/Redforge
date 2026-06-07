# Fact Checking and Validation

## Fact Sources

### Primary Sources
- CVE database
- OWASP documentation
- Official tool documentation
- RFC documents

### Secondary Sources
- Security blogs
- Research papers
- CTF writeups
- Expert opinions

## Validation Methods

### 1. Cross-Reference
```python
def cross_reference(fact, sources):
    confirmed = 0
    for source in sources:
        if verify(fact, source):
            confirmed += 1
    return confirmed / len(sources)
```

### 2. Authority Check
```python
def authority_score(source):
    authorities = {
        "nist.gov": 1.0,
        "owasp.org": 0.95,
        "cve.mitre.org": 0.95,
        "security_blog.com": 0.6,
        "forum.post": 0.3
    }
    return authorities.get(extract_domain(source), 0.5)
```

### 3. Freshness Check
```python
def is_fresh(document, max_age_days=365):
    if "published" in document:
        age = today - document["published"]
        return age.days < max_age_days
    return False
```

## Fact Categories

### Established Facts
- CVE descriptions
- Tool behavior documented
- Known attack patterns

### Debatable Facts
- Effectiveness of techniques
- Tool comparisons
- Best practices

### Disputed Facts
- Novel vulnerabilities
- Emerging techniques
- Unverified claims

## Confidence Levels

| Level | Meaning |
|-------|---------|
| High | Multiple authoritative sources |
| Medium | Single authoritative source |
| Low | Unverified or anecdotal |
| Unknown | Cannot verify |

## Validation Workflow

```
Fact → Identify Sources → Verify Each → Score → Confidence
```

## Best Practices

1. **Cite sources**: Always attribute information
2. **Check dates**: Prefer recent information
3. **Verify credentials**: Trust authoritative sources
4. **Acknowledge uncertainty**: When in doubt, say so
5. **Update regularly**: Facts can change

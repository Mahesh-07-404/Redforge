# Source Citation

## Citation Format

### Standard Citation
```
[Source] Title. Author/Organization. Date. URL
```

### Example
```
[1] OWASP. "SQL Injection Prevention Cheat Sheet." 2023. 
    https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
```

### Inline Citation
```
SQL injection occurs when user input is not properly sanitized [1].
```

## Citation Types

### Primary Sources
- CVE entries
- RFC documents
- Official documentation

### Secondary Sources
- Security blogs
- Research papers
- CTF writeups

### Tertiary Sources
- Summaries
- Tutorials
- Expert opinions

## Citation Quality

| Quality | Source Type | Reliability |
|---------|-------------|-------------|
| High | CVE, RFC, NIST | Very reliable |
| Medium | OWASP, MITRE | Reliable |
| Low | Blog, Forum | Verify independently |

## Citation Database

```python
citations = [
    {
        "id": "CVE-2023-1234",
        "type": "cve",
        "title": "SQL Injection in Example",
        "source": "cve.mitre.org",
        "date": "2023-01-15",
        "url": "https://cve.mitre.org/..."
    },
    {
        "id": "OWASP-SQLi",
        "type": "cheatsheet",
        "title": "SQL Injection Prevention",
        "source": "owasp.org",
        "date": "2023-06-01",
        "url": "https://cheatsheetseries.owasp.org/..."
    }
]
```

## Citation in Findings

```markdown
## Finding: SQL Injection in Login Form

**Severity:** Critical

**Evidence:**
- Database error on payload: `' OR 1=1--`
- Error message reveals SQL syntax

**Impact:**
- Authentication bypass [1]
- Data exfiltration [2]

**References:**
- [1] OWASP SQL Injection, https://owasp.org/www-community/attacks/SQL_Injection
- [2] PortSwigger SQL Injection, https://portswigger.net/web-security/sql-injection
```

## Best Practices

1. **Always cite**: Give credit to sources
2. **Use primary sources**: When available
3. **Verify URLs**: Links should work
4. **Include dates**: Information changes
5. **Note reliability**: Not all sources equal

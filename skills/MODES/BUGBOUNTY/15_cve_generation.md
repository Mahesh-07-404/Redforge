# CVE Generation

## Internal CVE Format

```json
{
  "cve_id": "INTERNAL-2024-001",
  "title": "SQL Injection in Login Form",
  "severity": "CRITICAL",
  "cvss_score": 9.8,
  "cwe": "CWE-89",
  "description": "SQL injection vulnerability...",
  "affected_versions": ["1.0.0 - 1.5.2"],
  "fixed_version": "1.5.3",
  "references": ["https://target.com/patch"],
  "discovered": "2024-01-15",
  "reporter": "RedForge"
}
```

## CNA Draft Structure

```markdown
## CVE Request

### Candidate Number
CANDIDATE-2024-XXXXX

### Product
Product Name and Version

### Vulnerability Type
SQL Injection

### Description
Detailed description...

### Affected Code
```python
# Vulnerable code
query = f"SELECT * FROM users WHERE id = {user_id}"
```

### Proof of Concept
```bash
curl "http://target.com/api/user/1' OR 1=1--"
```

### Credit
Your name/handle
```

## CVSS Calculation

| Score | Severity |
|-------|----------|
| 0.0-3.9 | Low |
| 4.0-6.9 | Medium |
| 7.0-8.9 | High |
| 9.0-10.0 | Critical |

## CVE Database

```python
cve_db = {
    "INTERNAL-2024-001": {
        "title": "...",
        "severity": "CRITICAL",
        "status": "discovered"
    }
}
```

## Submission Checklist

- [ ] Vulnerability description
- [ ] Affected versions
- [ ] Proof of concept
- [ ] CVSS score
- [ ] CWE classification
- [ ] Remediation

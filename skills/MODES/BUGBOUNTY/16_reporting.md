# BUGBOUNTY Skill: Reporting & Documentation

## Purpose
Create professional, detailed bug reports that maximize bounty rewards.

## Report Structure

### 1. Title (Clear & Concise)
```
Format: [Component] - [Vulnerability Type] on [Specific Endpoint]
Example: SQL Injection in /api/users/search parameter
```

### 2. Summary (3-4 Sentences)
- What the vulnerability is
- Where it exists (endpoint/feature)
- How it was discovered
- Potential impact

### 3. Severity Assessment
```
CVSS 3.1 Scoring:
- Attack Vector (Network/Adjacent/Local/Physical)
- Attack Complexity (Low/High)
- Privileges Required (None/Low/High)
- User Interaction (None/Required)
- Scope (Unchanged/Changed)
- Confidentiality/Integrity/Availability Impact
```

### 4. Steps to Reproduce
```
Format: Numbered, detailed, reproducible
1. Navigate to [URL]
2. Intercept request with proxy
3. Modify [parameter] to [malicious value]
4. Observe [result]
5. Confirm with [additional test]

Include:
- Exact URLs
- Request/Response examples
- Screenshots
- Video PoC (if complex)
```

### 5. Impact Analysis
- Data sensitivity exposed
- User accounts at risk
- Financial impact
- Regulatory implications
- Attack scenarios

### 6. Remediation Recommendations
```
Priority Order:
1. Immediate mitigation
2. Short-term fix
3. Long-term solution
4. Prevention measures

Include code examples if possible
```

### 7. Supporting Materials
- PCAP files
- Log excerpts
- Configuration files
- POC scripts
- Screenshots
- Video recordings

## Platform-Specific Guidelines

### HackerOne
- Use their report template
- Reference CWE types
- Include CVSS calculator
- Tag relevant programs
- Respond within 48 hours

### Bugcrowd
- VRT severity mapping
- Detailed reproduction steps
- Business impact focus
- Multiple PoC variants

### Private Programs
- More detailed reports allowed
- Include attack chains
- Suggest CVEs if applicable
- Request escalation timeline

## Common Report Mistakes
- ❌ Vague descriptions
- ❌ Missing reproduction steps
- ❌ No impact assessment
- ❌ Oversized attachments
- ❌ Demanding behavior
- ❌ Duplicate reports

## Best Practices
- ✅ Write for non-technical triagers first
- ✅ Include severity justification
- ✅ Provide actionable remediation
- ✅ Be responsive to questions
- ✅ Follow up appropriately
- ✅ Maintain professional tone

## Report Quality Checklist
```
[ ] Clear title
[ ] Summary under 100 words
[ ] CVSS score with vector
[ ] Step-by-step reproduction
[ ] Minimal screenshots (relevant only)
[ ] Real impact (not theoretical)
[ ] Actionable remediation
[ ] Proof of concept code
[ ] Requested bounty range
[ ] References/CVE links
```

## Response Templates

### Initial Submission
```
## Report: [Title]

**Severity:** [Critical/High/Medium/Low/Info]
**CVSS:** [Score] ([Vector])

### Summary
[Brief description]

### Steps to Reproduce
1. [Step]
...

### Impact
[Business impact]

### Remediation
[Fix suggestion]
```

### Follow-up Response
```
Thank you for the update.

I have [provided additional info/clarification].

[Specific question or concern]

Timeline expectation: [Requested]
```

### Severity Dispute
```
I would like to discuss the severity rating.

My reasoning:
1. [Point 1]
2. [Point 2]
3. [Point 3]

Evidence:
- [Link to impact analysis]
- [Supporting data]

Request: [Settlement amount or severity change]
```

## Bounty Negotiation
- Research similar payouts in VDP
- Provide additional attack vectors
- Quantify business impact
- Demonstrate expertise
- Be respectful but firm
- Know your value

## Timeline Expectations
| Phase | Expected Time |
|-------|--------------|
| Triager response | 1-7 days |
| Duplicate check | 1-14 days |
| Severity assessment | 7-30 days |
| Bounty determination | 14-60 days |
| Remediation verification | 30-90 days |

## Report Templates by Type

### Stored XSS
```markdown
## Stored XSS in [Feature]

**Endpoint:** /api/[endpoint]
**Parameter:** [param]
**Method:** POST

### Summary
Stored XSS in [feature] allows [impact].

### Steps to Reproduce
1. Navigate to [location]
2. Enter payload: <script>alert(document.domain)</script>
3. Submit and refresh page
4. XSS executes

### Impact
- Session hijacking
- Credential theft
- Malicious redirects

### Remediation
[Sanitization fix]
```

### SQL Injection
```markdown
## Blind SQL Injection in [Endpoint]

**Endpoint:** /api/[endpoint]
**Parameter:** [param]
**Method:** GET

### Summary
Parameter [param] is vulnerable to blind SQLi.

### Steps to Reproduce
1. GET /api/[endpoint]?[param]=1' AND SLEEP(5)--
2. Response delayed by 5 seconds
3. Confirmed SQLi with boolean-based tests

### Time Comparison
- Normal: ~200ms
- With SLEEP(5): ~5200ms

### Impact
- Database enumeration
- Data exfiltration
- Potential RCE

### Remediation
[Parameterized queries]
```

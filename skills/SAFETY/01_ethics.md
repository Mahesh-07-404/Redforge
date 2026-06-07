# SAFETY Skill: Ethical Guidelines

## Purpose
Ensure ethical conduct during all RedForge activities.

## Core Principles

### 1. Authorization
```
ALWAYS verify you have explicit permission before:
- Scanning networks
- Testing vulnerabilities
- Exploiting systems
- Accessing data
```

### 2. Scope Compliance
```
STRICTLY adhere to:
- Defined scope (IP ranges, domains)
- Allowed testing methods
- Time windows
- Rules of engagement
```

### 3. Data Handling
```
- Collect minimal necessary data
- Encrypt all stored data
- Delete after report
- Never exfiltrate personal data
- Respect PII/GDPR
```

## Bug Bounty Ethics

### Do
```
✓ Test only in-scope targets
✓ Follow program rules
✓ Report quickly
✓ Provide reproduction steps
✓ Suggest remediation
✓ Be professional
✓ Respect rate limits
```

### Don't
```
✗ Test out of scope
✗ Exploit for personal gain
✗ Access more data than needed
✗ Share findings with others
✗ DDOS or disrupt services
✗ Demand bounties
✗ Blackmail programs
```

## Responsible Disclosure

### Timeline
```
Day 0:   Discover vulnerability
Day 1:   Report to vendor/program
Day 7:   Follow up (if no response)
Day 30:  Public disclosure (if unfixed)
Day 90:  Full disclosure (typically)
```

### What to Include
```
- Clear description
- Steps to reproduce
- Proof of concept
- Impact assessment
- Suggested fix
- Screenshots/logs
```

## Legal Considerations

### Laws
```
- CFAA (US) - Computer Fraud and Abuse Act
- Computer Misuse Act (UK)
- GDPR (EU) - Data protection
- Local cyber laws
```

### Safe Harbor
```
Many programs offer safe harbor:
- Protects researchers
- Limits liability
- Check program's policy
```

## Prohibited Actions

### Never Do
```
1. Access data you shouldn't
2. Modify systems beyond testing
3. Social engineering without consent
4. Physical security testing without permission
5. DDoS attacks
6. Spam or harassment
7. Exfiltrate passwords or credentials
8. Leave backdoors
```

### Red Lines
```
- Financial fraud
- Identity theft
- Violating privacy
- Harassment
- Extortion
```

## Professional Conduct

### Communication
```
- Be clear and concise
- Be patient and respectful
- Provide evidence
- Accept feedback
- Don't burn bridges
```

### Competence
```
- Know your limits
- Don't guess
- Test before reporting
- Verify findings
- Keep skills updated
```

## Case Studies

### Good Example
```
"Found SQL injection in /api/users?id=1'
Successfully demonstrated impact by enumerating usernames.
Reported with full PoC and remediation suggestions.
```

### Bad Example
```
"Found vulnerability, send payment or I publish.
Your security is terrible. Give me $10,000."
```

## Resources

### Guidelines
```
- OWASP Code of Conduct
- Bugcrowd Community Guidelines
- HackerOne Disclosure Guidelines
- NIST Cybersecurity Framework
- PTES (Penetration Testing Execution Standard)
```

## RedForge Compliance

### In RedForge
```
- Set authorization level before testing
- Use scope command to define targets
- Enable only allowed modules
- Log all activities
- Generate compliant reports
```

### Configuration
```bash
# Set authorization
redforge config set authorization=scope_limited

# Set mode
redforge config set mode=bugbounty

# Enable logging
redforge config set log_level=debug
```

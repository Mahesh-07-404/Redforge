# SAFETY Skill: Ethics Framework

## Purpose
Ethical guidelines for security professionals.

## Core Principles

### 1. Integrity
```
- Be honest in all dealings
- Report findings accurately
- Don't exaggerate or minimize
- Maintain objectivity
```

### 2. Authorization
```
- Only test with permission
- Stay within scope
- Follow rules of engagement
- Document everything
```

### 3. Privacy
```
- Protect sensitive data
- Minimize data collection
- Secure handling of PII
- Respect confidentiality
```

### 4. Responsibility
```
- Report vulnerabilities properly
- Give credit to others
- Consider impacts
- Improve security overall
```

## Professional Conduct

### In Bug Bounty
```
Do:
- Follow program rules
- Test only in-scope targets
- Report responsibly
- Be professional

Don't:
- Access more data than needed
- Exploit for personal gain
- Demand payment
- Publicize before coordination
```

### In Pentesting
```
Do:
- Get written authorization
- Test only approved targets
- Minimize disruption
- Report comprehensively

Don't:
- Go beyond scope
- Cause unnecessary damage
- Share findings widely
- Withhold information
```

### In Research
```
Do:
- Coordinate disclosure
- Help vendors fix issues
- Share knowledge responsibly
- Mentor others

Don't:
- Publish 0-days freely
- Enable malicious use
- Harm users
- Seek fame over safety
```

## Ethical Dilemmas

### Scenario 1: Vulnerable System Found
```
Situation: During authorized test, you find a critical vulnerability
            that exposes massive PII data.

Decision Process:
1. Document the finding
2. Stop accessing data immediately
3. Report to authorization holder ASAP
4. Do not copy or exfiltrate data
5. Offer remediation guidance
6. Do not publicize
```

### Scenario 2: Out-of-Scope Discovery
```
Situation: Testing example.com, you find it vulnerable and isp.com
          is the hosting provider.

Decision Process:
1. Stop testing isp.com immediately
2. Document the finding
3. Report to example.com
4. Ask about scope expansion
5. Do not access isp.com
```

### Scenario 3: Sensitive Data Exposure
```
Situation: You accidentally access sensitive medical records during testing.

Decision Process:
1. Stop immediately
2. Do not save, copy, or view further
3. Document what you saw (minimally)
4. Report to authorization holder
5. Suggest immediate remediation
6. Request guidance on disclosure
```

### Scenario 4: Zero-Day Discovery
```
Situation: You find an unknown vulnerability in widely-used software.

Decision Process:
1. Do not publicize
2. Contact vendor directly
3. Provide detailed report
4. Coordinate disclosure timeline
5. Give reasonable time for fix
6. Consider CVEs for significant findings
```

## Building Trust

### With Clients
```
- Be transparent about methods
- Report all findings (good and bad)
- Meet commitments
- Provide actionable recommendations
- Maintain confidentiality
```

### With Community
```
- Share knowledge responsibly
- Help others learn
- Contribute to security improvements
- Follow responsible disclosure
```

### With Vendors
```
- Report professionally
- Give credit for fixes
- Coordinate timing
- Be available for questions
```

## Red Lines

### Never Do
```
1. Access systems without authorization
2. Exceed scope of testing
3. Publicize before coordination
4. Exploit for personal gain
5. Harm users or organizations
6. Withhold vulnerabilities
7. Lie about findings
8. Blackmail or extort
```

## Ethical Decision Framework

### Questions to Ask
```
1. Do I have authorization?
2. Is this within scope?
3. What is the impact if misused?
4. How would this look publicly?
5. Am I following professional standards?
6. Would I be comfortable if this was my data?
7. Is there a better way to handle this?
```

### When Unsure
```
1. Stop
2. Document
3. Consult
4. Wait
5. Then proceed
```

## Professional Development

### Certifications
```
- OSCP, CEH, CISSP (ethics requirements)
- CPE requirements
- Continuous learning
```

### Community Standards
```
- OWASP guidelines
- Full disclosure guidelines
- Industry best practices
```

## Review Questions

### Before Each Test
```
[ ] Do I have authorization?
[ ] Is everything documented?
[ ] Do I understand the scope?
[ ] Are emergency contacts known?
[ ] Do I know the rules?
```

### During Testing
```
[ ] Am I staying in scope?
[ ] Is my impact minimal?
[ ] Am I documenting findings?
[ ] Do I need to stop?
```

### After Testing
```
[ ] Did I follow all rules?
[ ] Is the report accurate?
[ ] Were findings properly disclosed?
[ ] Did I maintain confidentiality?
```

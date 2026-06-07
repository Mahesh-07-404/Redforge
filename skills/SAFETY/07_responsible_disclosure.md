# SAFETY Skill: Responsible Disclosure

## Purpose
Handle vulnerability disclosure properly.

## Disclosure Timeline

### Standard Timeline
```
Day 0:   Discover vulnerability
Day 1:   Report to vendor/program
Day 7:   Follow up (if no response)
Day 14:  Second follow up
Day 30:  Public disclosure (if fixed)
Day 90:  Full public disclosure
```

### Escalation Path
```
1. Vendor direct (primary)
2. CERT/CC (if vendor unresponsive)
3. Public disclosure (last resort)
```

## Reporting Templates

### Initial Report
```markdown
## Vulnerability Report

**Product:** [Name and Version]
**Date:** [Discovery Date]
**Reporter:** [Your Name/Contact]

### Summary
[Brief description of the vulnerability]

### Technical Details
[Detailed explanation with affected components]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Proof of Concept
[POC code, screenshots, videos]

### Impact
[Security and business impact]

### Remediation
[Suggested fix or mitigation]

### Timeline
- [Date]: Vulnerability discovered
- [Date]: Vendor contacted
```

### Follow-up Template
```markdown
## Follow-up #1

Date: [Date]
Original Report Date: [Date]
Status: [Acknowledged/Fixed/Pending]

Updates:
[Any new information or changes]

Request:
[What you're asking for]
```

## Communication Tips

### Do
```
- Be professional and courteous
- Provide clear reproduction steps
- Offer remediation suggestions
- Be patient
- Respond promptly to questions
- Keep communication channels private
```

### Don't
```
- Demand immediate response
- Threaten disclosure
- Publicize before coordinator
- Demand bounties
- Be rude or aggressive
- Exploit beyond testing
```

## Public Disclosure

### When Appropriate
```
1. Vendor acknowledged (even if not fixed)
2. Time limit exceeded
3. Public interest
4. Active exploitation known
```

### Partial Disclosure
```
- Don't provide full PoC
- Describe vulnerability class
- Don't name affected products
- Give vendor time to respond
```

## Coordinated Disclosure

### CERT/CC
```markdown
To: cert@cert.org
Subject: Coordinated Vulnerability Report

Report the following vulnerability for coordination.
[Follow report template]
```

### NIST CVD Program
```markdown
# For critical infrastructure
Contact: nvd@nist.gov
Follow NIST guidelines
```

## Bug Bounty Specific

### Platform Guidelines
```
- HackerOne: Follow their disclosure policy
- Bugcrowd: Respect their timeline
- Private programs: Follow program rules
```

### Best Practices
```
1. Follow platform disclosure rules
2. Wait for patch before full details
3. Give credit where due
4. Update report with fix verification
```

## Documentation

### Keep Records
```
1. All communications
2. Timeline of events
3. Version history
4. Remediation verification
5. Public disclosure notice
```

## CVEs

### When to Request
```
- Significant vulnerability
- Public disclosure
- Vendor requests
- Industry impact
```

### CVE Request Process
```
1. Contact vendor for CNA
2. Request CVE from MITRE
3. Provide detailed information
4. Wait for assignment
```

## Checklist
```
[ ] Written report to vendor
[ ] Proof of delivery
[ ] Response tracking
[ ] Follow-up schedule
[ ] Disclosure timeline
[ ] Public notice preparation
[ ] CVE request (if needed)
```

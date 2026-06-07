# Ethics and Safety Guidelines

## Core Principles

### 1. Authorization First
**Never** test systems without explicit authorization.

### 2. Scope Compliance
Only test targets explicitly authorized and within defined scope.

### 3. Minimal Impact
Minimize disruption to target systems.

### 4. Responsible Disclosure
Follow coordinated disclosure practices.

### 5. User Safety
Prioritize safety over finding vulnerabilities.

## Strict Rules

### NEVER Do
- Test systems you don't own without written authorization
- Attack infrastructure outside defined scope
- Access data beyond authorized targets
- Disrupt services or deny access
- Exfiltrate sensitive data
- Share findings without consent
- Use discovered vulnerabilities maliciously

### ALWAYS Do
- Verify authorization before testing
- Document scope boundaries
- Use least-invasive techniques first
- Stop immediately if requested
- Provide detailed findings documentation
- Follow responsible disclosure timelines

## Legal Compliance

### Jurisdiction Awareness
- Know local laws (CFAA, Computer Fraud Act, etc.)
- Understand international considerations
- Consider GDPR for EU targets

### Documentation Requirements
- Keep authorization documentation
- Record all testing activities
- Maintain audit trail

## Safety Features

### Autonomy Restrictions
- MANUAL: Maximum safety, all actions confirmed
- PARTIAL: Safe actions auto-execute, dangerous actions confirmed
- FULL: Autonomous (requires explicit consent)

### Loop Detection
- Maximum iterations enforced
- State change monitoring
- Automatic escalation on stagnation

### Scope Enforcement
- Target validation
- Scope boundary checks
- Out-of-scope warnings

## Ethical Decision Framework

When uncertain about an action:

1. **Is it authorized?** → No → Stop
2. **Is it within scope?** → No → Stop
3. **Is it destructive?** → Unknown → Ask
4. **Is user informed?** → No → Inform first
5. **Is it reversible?** → No → Get explicit approval

## Reporting Concerns

If you discover:
- Child exploitation material → Report immediately
- Critical infrastructure vulnerabilities → Follow responsible disclosure
- Evidence of illegal activity → Stop and advise user to contact authorities

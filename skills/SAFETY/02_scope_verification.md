# SAFETY Skill: Scope Verification

## Purpose
Properly define and verify testing scope.

## Scope Definition

### What is Scope?
```
Explicitly authorized targets for testing:
- IP addresses/ranges
- Domain names
- Subdomains
- API endpoints
- Mobile apps
```

### Scope Types
```
In-Scope:     Authorized to test
Out-of-Scope: NOT authorized
Sensitive:    Extra caution required
Critical:     Highest risk targets
```

## Bug Bounty Programs

### Common Scope
```
In-Scope Example:
- *.example.com
- api.example.com
- https://example.com
- Mobile apps (Android/iOS)

Out-of-Scope:
- staging.example.com
- dev.example.com
- Third-party services
```

### Reading Program Rules
```
1. Check allowed testing methods
2. Note rate limits
3. Check restricted techniques
4. Review disclosure policy
5. Check safe harbor terms
```

## Scope Commands

### RedForge Scope
```bash
# Set scope
redforge scope add domain:example.com
redforge scope add ip:192.168.1.0/24
redforge scope add subdomain:*.example.com

# List scope
redforge scope list

# Verify scope
redforge scope verify

# Export scope
redforge scope export
```

### Verify Target
```bash
# Check if in scope
redforge scope check example.com

# Check for conflicts
redforge scope audit
```

## Scope Enumeration

### Passive Recon
```bash
# Don't actively scan
# Only use public information
# Examples:
# - WHOIS records
# - DNS records
# - Public leakage
# - Archive.org
```

### Active Recon
```bash
# Requires authorization
# Can include:
# - Port scanning
# - Vulnerability scanning
# - Exploitation
```

## Common Mistakes

### Misconfiguration
```bash
# ❌ Testing without scope
redforge scan 192.168.1.1

# ✓ First define scope
redforge scope add ip:192.168.1.1
redforge scan 192.168.1.1
```

### Assumption
```bash
# ❌ Assuming adjacent IPs are in scope
# ✓ Always verify explicitly
redforge scope check 192.168.1.5
```

### Documentation
```bash
# ❌ No documentation
# ✓ Save scope evidence
redforge scope list > scope.txt
```

## Scope Creep

### What is Scope Creep?
```
Testing beyond authorized boundaries:
- Testing .com when only .org authorized
- Accessing systems via pivoted access
- Using stolen credentials
```

### Prevention
```
1. Document scope clearly
2. Verify before testing
3. Stop at boundaries
4. Ask for clarification
```

## Authorization Levels

### None (Forbidden)
```
No permission to test
Public bug bounties only
Respect robots.txt
```

### Limited
```
Only specified targets
Follow all rules
Report only findings
```

### Full
```
Authorized internal testing
Extended permissions
Comprehensive testing
```

### Compliance
```
Always match your authorization:
- RedForge respects authorization level
- Mode selection affects capabilities
- Violation triggers warnings
```

## Practical Examples

### Bug Bounty Scope
```bash
# Program: example.com
# Rules: No DoS, no social engineering

# Valid targets:
example.com
www.example.com
api.example.com

# Invalid (out of scope):
staging.example.com
dev.example.com
s3.example.com (if not listed)
```

### CTF/Internal
```bash
# Training environment
# Full scope of challenge VMs

# Example:
# Only hack the CTF network
# Not the organizer network
```

## Scope Conflicts

### What to Do
```
1. Stop immediately
2. Document what happened
3. Report to program/organization
4. Don't share findings
5. Wait for guidance
```

### Gray Areas
```
If uncertain:
- Don't test
- Ask for clarification
- Document the question
```

## RedForge Safety Features

### Auto-Protection
```
- Scope boundaries enforced
- Out-of-scope warnings
- Blocked commands
- Audit logging
```

### Configuration
```bash
# Enable scope enforcement
redforge config set enforce_scope=true

# Set warning level
redforge config set scope_warning=strict
```

## Checklist
```
[ ] Read all program rules
[ ] List all in-scope targets
[ ] Note all restrictions
[ ] Save scope documentation
[ ] Verify before testing
[ ] Stay within boundaries
[ ] Report scope questions
```

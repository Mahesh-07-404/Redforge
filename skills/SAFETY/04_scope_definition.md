# SAFETY Skill: Scope Definition

## Purpose
Define and manage testing scope properly.

## What is Scope?

### Definition
```
Authorized targets for security testing
IP addresses, domains, subdomains, applications
```

### Why It Matters
```
1. Legal protection
2. Avoids unintended damage
3. Focuses testing efforts
4. Professional standards
```

## Scope Elements

### IP Addresses
```yaml
scope:
  ip_addresses:
    - 192.168.1.1
    - 10.0.0.0/24
    - 172.16.0.0/12
```

### Domain Names
```yaml
scope:
  domains:
    - example.com
    - api.example.com
    - www.example.com
```

### Subdomains
```yaml
scope:
  subdomains:
    - "*.example.com"
    - "*.staging.example.com"
```

### URLs
```yaml
scope:
  urls:
    - https://example.com/*
    - https://api.example.com/v1/*
```

## Exclusions

### Always Exclude
```
- Production databases (unless explicitly allowed)
- Critical infrastructure
- 911/emergency services
- Government systems
- Healthcare critical systems
```

### Exclude Example
```yaml
scope:
  exclude:
    - dev.example.com  # Dev not in scope
    - 10.0.0.1        # Database server
    - staging.internal.local
```

## RedForge Scope Commands

### Add to Scope
```bash
# Add domain
redforge scope add domain:example.com

# Add IP range
redforge scope add ip:192.168.1.0/24

# Add subdomain
redforge scope add subdomain:*.example.com

# Add URL
redforge scope add url:https://api.example.com/*
```

### Manage Scope
```bash
# List scope
redforge scope list

# Remove from scope
redforge scope remove example.com

# Verify scope
redforge scope verify

# Export scope
redforge scope export > scope.txt
```

## Scope Verification

### Before Testing
```bash
# Verify target is in scope
redforge scope check target.com

# Check for conflicts
redforge scope audit

# Validate scope file
redforge scope validate scope.yaml
```

### Verification Checklist
```
[ ] All targets documented
[ ] No production systems
[ ] Exclusions noted
[ ] Authorization written
[ ] Scope reviewed by stakeholders
```

## Scope Creep

### What is Creep?
```
Testing beyond authorized boundaries
Often unintentional
Can cause legal issues
```

### Prevention
```
1. Document everything
2. Verify before testing
3. Ask for clarification
4. Stop at boundaries
5. Report scope questions
```

### Handling Ambiguity
```
1. Don't assume
2. Ask explicitly
3. Get written confirmation
4. Document the question
5. Wait for response
```

## Bug Bounty Scope

### Typical Scope
```yaml
program:
  name: Example Program
  targets:
    in_scope:
      - domain: example.com
        type: website
      - domain: api.example.com
        type: api
      - domain: "*.mobile.example.com"
        type: android-ios
    out_of_scope:
      - staging.example.com
      - dev.example.com
```

### Rules
```
- Only test in-scope targets
- Follow rate limits
- Don't impact availability
- Report immediately if unsure
```

## CTF Scope

### Typical Scope
```yaml
competition:
  network: 10.10.10.0/24
  allowed:
    - All hosts in network
    - Services on those hosts
  prohibited:
    - Infrastructure hosts
    - Score server
    - Team networks
```

## Authorization Levels

### None
```
No permission
Only public bug bounties
```

### Limited
```
Specific targets
Specific techniques
Specific time period
```

### Full
```
Internal pentesting
Extended permissions
Comprehensive testing
```

## Documentation

### Scope Document
```markdown
# Security Testing Scope

## Authorization
- Organization: Example Corp
- Tester: [Your Name]
- Period: 2024-01-01 to 2024-01-31
- Type: External Penetration Testing

## In-Scope Targets
| Target | Type | Criticality |
|--------|------|-------------|
| example.com | Web | High |
| api.example.com | API | High |
| 10.0.0.0/24 | Network | Medium |

## Out-of-Scope
- staging.example.com
- dev.internal.com

## Exclusions
- Do not test production databases directly
- Limit concurrent connections

## Authorization Contact
- Name: Security Team
- Email: security@example.com
- Phone: +1-555-1234
```

## Checklist
```
[ ] Written authorization obtained
[ ] All targets documented
[ ] Exclusions clearly marked
[ ] Time period specified
[ ] Contact information available
[ ] Scope reviewed and approved
[ ] Document stored securely
```

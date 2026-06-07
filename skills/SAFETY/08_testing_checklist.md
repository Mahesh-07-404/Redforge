# SAFETY Skill: Security Testing Checklist

## Purpose
Comprehensive security testing checklist.

## Pre-Engagement

### Authorization
```
[ ] Written authorization obtained
[ ] Scope clearly defined
[ ] Time period established
[ ] Emergency contacts known
[ ] Rules of engagement documented
```

### Scope Verification
```
[ ] IP ranges confirmed
[ ] Domains listed
[ ] Applications specified
[ ] Exclusions noted
[ ] Physical locations (if applicable)
```

### Preparation
```
[ ] Tools updated
[ ] Environment ready
[ ] Team briefed
[ ] Documentation prepared
[ ] Communication channels established
```

## Information Gathering

### Passive Recon
```
[ ] WHOIS records
[ ] DNS records
[ ] Subdomain enumeration
[ ] Archive.org
[ ] Social media
[ ] Public documents
```

### Active Recon
```
[ ] Port scanning
[ ] Service enumeration
[ ] Technology fingerprinting
[ ] Directory enumeration
[ ] Parameter discovery
```

## Network Testing

### External Network
```
[ ] Firewall rules
[ ] Open ports
[ ] Service versions
[ ] VPN access
[ ] Remote services
```

### Internal Network
```
[ ] Lateral movement paths
[ ] Privilege escalation
[ ] Credential access
[ ] Domain enumeration
[ ] Network segmentation
```

## Web Application

### Authentication
```
[ ] Registration/login
[ ] Password reset
[ ] MFA implementation
[ ] Session management
[ ] Account lockout
```

### Authorization
```
[ ] IDOR
[ ] Privilege escalation
[ ] Horizontal access
[ ] Vertical access
[ ] Direct object reference
```

### Input Validation
```
[ ] SQL injection
[ ] XSS (reflected, stored, DOM)
[ ] Command injection
[ ] LDAP injection
[ ] XML injection
[ ] SSRF
```

### Business Logic
```
[ ] Workflow bypasses
[ ] Race conditions
[ ] Time-of-check issues
[ ] Financial logic
[ ] File upload validation
```

## API Security

### REST API
```
[ ] Authentication
[ ] Authorization
[ ] Rate limiting
[ ] Input validation
[ ] Output encoding
[ ] Versioning
```

### GraphQL
```
[ ] Introspection
[ ] Authorization
[ ] Batching attacks
[ ] Alias attacks
[ ] Query complexity
```

## Mobile Security

### Android
```
[ ] APK analysis
[ ] Hardcoded secrets
[ ] SSL pinning
[ ] Data storage
[ ] Intent handling
[ ] Native libraries
```

### iOS
```
[ ] IPA analysis
[ ] Keychain usage
[ ] SSL pinning
[ ] Data storage
[ ] IPC mechanisms
```

## Cloud Security

### AWS
```
[ ] IAM policies
[ ] S3 buckets
[ ] EC2 security
[ ] Lambda functions
[ ] CloudTrail logs
```

### Azure/GCP
```
[ ] IAM configurations
[ ] Storage access
[ ] Compute instances
[ ] Network security
[ ] Logging/monitoring
```

## Cryptography

### Implementation
```
[ ] Weak algorithms
[ ] Key management
[ ] Random number generation
[ ] Protocol issues
[ ] Certificate validation
```

### Storage
```
[ ] Password hashing
[ ] Encryption at rest
[ ] Key storage
[ ] Secrets management
```

## Social Engineering

### Phishing
```
[ ] Email security
[ ] Impersonation
[ ] Credential harvesting
[ ] Malicious attachments
```

### Physical
```
[ ] Badge access
[ ] Tailgating
[ ] Dumpster diving
[ ] Shoulder surfing
```

## Post-Testing

### Documentation
```
[ ] Findings organized
[ ] Evidence collected
[ ] Screenshots saved
[ ] PoC created
[ ] Report drafted
```

### Remediation
```
[ ] Findings shared
[ ] Priority set
[ ] Timeline agreed
[ ] Verification planned
```

## Reporting

### Executive Summary
```
[ ] High-level findings
[ ] Business impact
[ ] Risk assessment
[ ] Recommendations
```

### Technical Details
```
[ ] Finding descriptions
[ ] Steps to reproduce
[ ] Impact analysis
[ ] Remediation steps
```

### Appendices
```
[ ] Raw data
[ ] Tool outputs
[ ] References
[ ] Glossary
```

## Follow-up

### Verification
```
[ ] Re-test fixed vulnerabilities
[ ] Confirm remediation
[ ] Update report
[ ] Final sign-off
```

### Lessons Learned
```
[ ] What went well
[ ] What to improve
[ ] Process updates
[ ] Tool improvements
```

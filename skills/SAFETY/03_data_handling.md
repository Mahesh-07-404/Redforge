# SAFETY Skill: Data Handling

## Purpose
Properly handle sensitive data during security testing.

## Data Classification

### Types
```
Public:     Information freely available
Internal:   Business information
Confidential: Sensitive business data
PII:        Personally Identifiable Information
PHI:        Protected Health Information
```

## Data Handling Rules

### During Testing
```
1. Minimize collection
2. Process only what's needed
3. Don't store unnecessarily
4. Encrypt in memory
5. Don't screenshot unless needed
```

### After Testing
```
1. Securely delete findings
2. Clear temporary files
3. Remove from logs
4. Report only necessary details
```

## Sensitive Data Types

### Credentials
```
- Passwords
- API keys
- Tokens
- Certificates
- SSH keys
```

### Personal Data
```
- Names
- Addresses
- Phone numbers
- Email addresses
- Social security numbers
- Financial data
```

### Business Data
```
- Trade secrets
- Proprietary code
- Business strategies
- Customer lists
- Financial records
```

## What to Include in Reports

### Do Include
```
✓ Vulnerability details
✓ Impact assessment
✓ Reproduction steps
✓ General affected systems
✓ Suggested remediation
```

### Don't Include
```
✗ Actual passwords/credentials
✗ Full dump of personal data
✗ Unredacted PII
✗ Proprietary source code
✗ Sensitive business documents
```

## Redaction

### How to Redact
```
Before: john.doe@email.com
After:  j***@***.com

Before: 192.168.1.100
After:   192.168.1.***

Before: SSN: 123-45-6789
After:   SSN: ***-**-6789
```

### Tools
```bash
# PDF redaction
pdftk document.pdf redact

# Image redaction
# Use GIMP or ImageMagick
```

## Storage Security

### Encrypted Storage
```bash
# Encrypted container
veracrypt --create vault.hc
veracrypt vault.hc

# Encrypted files
gpg --encrypt findings.txt
```

### Secure Deletion
```bash
# Secure wipe
shred -v -n 1 findings.txt

# Tools
# BleachBit
# Eraser
```

## PII Protection

### GDPR Considerations
```
- Lawful basis required
- Data minimization
- Right to be forgotten
- Notification requirements
```

### Best Practices
```
1. Don't collect if not needed
2. Anonymize before storage
3. Encrypt at rest
4. Limit access
5. Delete when done
```

## Handling Leaks

### If You Find Data Breaches
```
1. Stop testing immediately
2. Document what you accessed
3. Report to organization ASAP
4. Don't share with anyone
5. Follow responsible disclosure
```

### Legal Considerations
```
- Unauthorized access laws
- Computer Fraud and Abuse Act
- Data protection regulations
- Notification requirements
```

## Evidence Handling

### Chain of Custody
```
1. Document all access
2. Timestamp findings
3. Use hash verification
4. Secure storage
5. Limited access
```

### Forensics
```bash
# Hash evidence
md5sum findings.txt
sha256sum findings.txt

# Store hashes
echo "abc123... findings.txt" > hashes.txt
```

## RedForge Data Handling

### Configuration
```bash
# Set data retention
redforge config set data_retention=delete_on_exit

# Enable encryption
redforge config set encrypt_finds=true

# Set PII detection
redforge config set pii_detection=strict
```

### Commands
```bash
# Clear findings
redforge data clear

# Export securely
redforge export --encrypted

# Purge all
redforge data purge
```

## Common Mistakes

### Bad Practices
```
❌ Screenshot everything "just in case"
❌ Store in unencrypted USB
❌ Share via unencrypted email
❌ Keep data after report
❌ Discuss findings publicly
```

### Good Practices
```
✓ Only collect what's needed
✓ Encrypt everything
✓ Use secure channels
✓ Delete after use
✓ Follow NDAs
```

## Compliance

### Frameworks
```
- ISO 27001
- SOC 2
- GDPR
- HIPAA
- PCI DSS
```

### Requirements
```
- Encryption standards
- Access controls
- Retention policies
- Breach notification
```

## Checklist
```
[ ] Minimize data collection
[ ] Encrypt sensitive findings
[ ] Redact PII in reports
[ ] Use secure storage
[ ] Delete after use
[ ] Document data handling
```

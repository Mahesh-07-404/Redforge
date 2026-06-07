# SAFETY Skill: Data Privacy

## Purpose
Handle sensitive data during security testing.

## Data Classification

### Public
```
- Information freely available
- No harm if disclosed
- Examples: Public records, job postings
```

### Internal
```
- Business information
- Not for public release
- Examples: org charts, policies
```

### Confidential
```
- Sensitive business data
- Limited access
- Examples: financials, strategy
```

### Restricted
```
- Highly sensitive
- Strict access controls
- Examples: PII, PHI, credentials
```

## PII Types

### Direct Identifiers
```
- Name
- Social Security Number
- Email address
- Phone number
- Physical address
- Driver's license
```

### Indirect Identifiers
```
- Date of birth
- Gender
- Race/ethnicity
- ZIP code
- Employment information
```

### Sensitive Categories
```
- Financial data
- Medical records
- Biometric data
- Genetic information
- Sexual orientation
```

## Handling During Testing

### Minimize Collection
```
- Only collect what's needed
- Don't save full data dumps
- Use sampling when possible
- Delete after verification
```

### Protect Storage
```
- Encrypted storage only
- Secure deletion
- Access controls
- No cloud storage
```

### Protect Transit
```
- Encrypted channels
- No email for findings
- Secure file transfer
- VPN for remote access
```

## Legal Requirements

### GDPR (EU)
```
- Lawful basis required
- Data minimization
- Right to erasure
- Breach notification (72 hours)
```

### CCPA (California)
```
- Consumer rights
- Opt-out requirements
- Privacy notices
```

### HIPAA (US)
```
- PHI protection
- Business associates
- Breach notification
```

### PCI DSS
```
- Cardholder data
- Network security
- Access controls
```

## Finding Handling

### What to Include
```
✓ Vulnerability details
✓ Affected system type
✓ General impact
✓ Reproduction steps
✓ Remediation
```

### What NOT to Include
```
✗ Actual SSNs
✗ Full credit card numbers
✗ Unredacted passwords
✗ Complete database dumps
✗ Medical record contents
```

## Redaction Techniques

### SSN
```
Before: 123-45-6789
After:  ***-**-6789
```

### Email
```
Before: john.doe@example.com
After:  j***@***.com
```

### IP Address
```
Before: 192.168.1.100
After:   192.168.1.**
```

### Phone
```
Before: +1-555-123-4567
After:   +1-555-***-****
```

## Secure Storage

### Encrypted Container
```bash
# VeraCrypt
veracrypt --create vault.hc
veracrypt vault.hc

# LUKS
cryptsetup luksFormat vault.img
```

### Encrypted Files
```bash
# GPG
gpg --encrypt --recipient key findings.txt

# OpenSSL
openssl enc -aes-256-cbc -salt -in findings.txt -out findings.enc
```

## Secure Deletion

### Tools
```bash
# shred
shred -v -n 3 findings.txt

# wipe
wipe -rf findings/

# Secure empty trash
rm -P findings.txt
```

### Verification
```bash
# Check deletion
strings findings.txt | grep -i "sensitive"
```

## Report Generation

### Safe Report Template
```markdown
## Finding: SQL Injection

**Severity:** High
**CVSS:** 8.2
**Affected:** /api/users endpoint

### Description
[Description without actual data]

### Impact
[Generic impact description]

### Steps to Reproduce
[Generic steps, no real data]

### Remediation
[Technical fix]
```

## Breach Response

### If You Cause a Breach
```
1. Stop immediately
2. Notify organization
3. Document what happened
4. Assist with response
5. Follow legal requirements
```

## Best Practices

### During Testing
```
1. Assume all data is sensitive
2. Collect minimal necessary data
3. Verify don't need before access
4. Encrypt everything stored
5. Delete when no longer needed
```

### In Reports
```
1. Redact all PII
2. Use generic examples
3. Don't include raw data
4. Provide summaries only
5. Use CVSS for impact
```

## Checklist
```
[ ] Minimize data collection
[ ] Encrypt all stored findings
[ ] Redact PII in reports
[ ] Secure deletion after use
[ ] Legal compliance check
[ ] Access controls in place
[ ] Training completed
```

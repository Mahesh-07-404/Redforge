# LEARNING Skill: Social Engineering Basics

## Purpose
Learn social engineering concepts and defense.

## Attack Vectors

### Phishing
```
Email-based attacks
Fake login pages
Malicious attachments
Clone legitimate sites
```

### Pretexting
```
Creating fake scenarios
Impersonating authority
Building false trust
```

### Baiting
```
Free USB drives
Infected downloads
Physical access attacks
```

### Tailgating
```
Following authorized personnel
Physical facility access
```

## Phishing Analysis

### Red Flags
```
Urgency/threats
Spelling/grammar errors
Suspicious sender
Generic greetings
Suspicious links
```

### URL Analysis
```bash
# Hover to check
# Look for homograph attacks
# Check subdomain
# Verify with VirusTotal
```

## Common Tools

### Social Engineering
```
SET (Social Engineering Toolkit)
Gophish
King Phisher
Maltego
theHarvester
```

### SET Example
```bash
# Start SET
setoolkit

# Options:
# 1. Social-Engineering Attacks
# 2. Penetration Testing (Fast-Track)
```

## OSINT for SE

### Information Gathering
```bash
# Email harvest
theHarvester -d target.com -b all

# LinkedIn scraping
# People data
# Company structure
```

### Targets
```
Employees
IT administrators
Executives
Help desk
```

## Defense

### Technical Controls
```
DMARC, DKIM, SPF
Email filtering
URL analysis tools
Multi-factor authentication
```

### User Training
```
Regular awareness
Phishing simulations
Reporting procedures
Security culture
```

### Incident Response
```
Report button
Quick response
Forensic analysis
```

## Vishing (Voice Phishing)

### Techniques
```
Caller ID spoofing
Voice cloning
Authority impersonation
Technical support scams
```

### Defense
```
Verify callback numbers
Use official channels
Don't give sensitive info
```

## Smishing (SMS Phishing)

### Characteristics
```
Short URLs
Urgency
Prize notifications
Package delivery
```

## Physical Security

### Badge Cloning
```
RFID readers
Clone badges
Tailgating
```

### Pretexting
```
Bypassing reception
Fake maintenance
Delivery pretexts
```

## Documentation
```
Log all attempts
Report to security
Preserve evidence
Train based on findings
```

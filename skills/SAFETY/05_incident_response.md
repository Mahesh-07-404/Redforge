# SAFETY Skill: Incident Response

## Purpose
Handle security testing incidents properly.

## What is an Incident?

### During Testing
```
- Accidental service disruption
- Data exposure
- Unauthorized access
- Detection/alert triggers
- Legal concerns
```

### Severity Levels
```
Critical: Immediate harm, stop testing
High:     Significant impact, pause
Medium:   Minor issue, document and continue
Low:      Informational, continue
```

## Immediate Response

### Step 1: Stop
```bash
# Stop all testing immediately
# Do not continue or try to fix
# Document what happened
```

### Step 2: Assess
```bash
# What happened?
# What was affected?
# What data was accessed?
# What was the impact?
```

### Step 3: Communicate
```bash
# Contact authorization holder immediately
# Provide clear description
# Follow their guidance
```

## Communication Template

### Initial Report
```markdown
Subject: Security Test Incident - Immediate Attention Required

Date/Time: [When it happened]
Contact: [Your name]
Test: [What you were doing]

Incident Description:
[What happened]

Impact Assessment:
[What was affected]

Actions Taken:
[What you've done so far]

Requested Guidance:
[What you need from them]
```

## Common Incidents

### Accidental Data Access
```
1. Stop accessing data
2. Don't copy or save
3. Document what you saw
4. Report immediately
5. Follow instructions
```

### Service Disruption
```
1. Stop all requests
2. Document the request that caused it
3. Report immediately
4. Wait for guidance
5. Do not attempt to restart
```

### Detection by Defender
```
1. Stop testing
2. Document what triggered detection
3. Report to authorization holder
4. May need to:
   - Wait for authorization
   - Adjust techniques
   - Continue with notification
```

### Unauthorized System Access
```
1. Stop immediately
2. Don't explore further
3. Document findings
4. Report immediately
5. Do not access more systems
```

## Documentation

### Incident Log
```markdown
# Incident Report

## Basic Info
- Date: YYYY-MM-DD
- Time: HH:MM UTC
- Tester: Name
- Contact: email/phone

## Incident Details
- Type: [Accidental access/Data exposure/etc.]
- Target: [What was affected]
- What Happened: [Description]
- Duration: [How long did it last]

## Data Involved
- Type: [Personal/Financial/etc.]
- Quantity: [How much]
- Access Method: [How you accessed]

## Actions Taken
1. Stopped testing
2. Documented findings
3. Contacted [Name] at [Time]
4. Awaiting guidance

## Root Cause
[Why did this happen]

## Recommendations
[How to prevent this]
```

## Post-Incident

### Review
```
1. What went wrong?
2. How to prevent?
3. Update procedures?
4. Improve safety measures?
```

### Follow Up
```
1. Document lessons learned
2. Update scope/rules if needed
3. Improve safety tools
4. Brief team members
```

## RedForge Incident Handling

### Built-in Features
```bash
# Incident mode
redforge incident --mode emergency

# Auto-pause testing
redforge config set incident_pause true

# Emergency stop
redforge emergency-stop

# Incident report template
redforge incident template
```

### Configuration
```yaml
incident:
  auto_pause: true
  emergency_contacts:
    - name: Security Team
      phone: +1-555-0100
      email: security@example.com
  documentation: required
```

## Prevention

### Before Testing
```
1. Review scope carefully
2. Test in safe environment first
3. Set rate limits
4. Use safe techniques
5. Have emergency contacts ready
```

### During Testing
```
1. Monitor for anomalies
2. Check before destructive tests
3. Stay within scope
4. Document everything
5. Pause if unsure
```

### Safety Checks
```
- Verify targets before scanning
- Use --safe-options in tools
- Enable rate limiting
- Monitor responses for errors
- Stop on first anomaly
```

## Legal Considerations

### Documentation Importance
```
- Proves good faith
- Shows professional conduct
- Protects you legally
- Helps organization
```

### Key Documentation
```
- Authorization letter
- Scope agreement
- Communication records
- Activity logs
- Incident reports
```

## Checklist
```
[ ] Stop testing immediately
[ ] Assess severity
[ ] Document everything
[ ] Contact authorization holder
[ ] Follow guidance
[ ] Complete incident report
[ ] Review and improve procedures
```

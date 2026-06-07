# LEARNING Skill: API Security Basics

## Purpose
Learn API security fundamentals.

## REST API

### Methods
```
GET    - Retrieve resource
POST   - Create resource
PUT    - Update (full)
PATCH  - Update (partial)
DELETE - Remove resource
```

### Status Codes
```
200 - OK
201 - Created
204 - No Content
400 - Bad Request
401 - Unauthorized
403 - Forbidden
404 - Not Found
500 - Server Error
```

## Common Vulnerabilities

### Broken Object Level Authorization (BOLA)
```
GET /api/users/123  → Shows user 123
GET /api/users/124 → Shows user 124 (vulnerable!)
```

### Broken Authentication
```
Weak passwords
Token leakage
No rate limiting
Session fixation
```

### Excessive Data Exposure
```
Returns all fields
Includes sensitive data
No field filtering
```

### Lack of Rate Limiting
```
No request limits
Brute force possible
DDoS vulnerable
```

### Mass Assignment
```
User object: {name, role}
Attacker sends: {name, role: "admin"}
```

## Authentication

### API Keys
```http
X-API-Key: your-api-key-here
```

### Bearer Tokens
```http
Authorization: Bearer <token>
```

### JWT
```javascript
// Structure
header.payload.signature

// Vulnerable to:
// - None algorithm
// - Key confusion
// - Weak secrets
```

## Rate Limiting

### Implementation
```python
from flask_limiter import Limiter
limiter = Limiter(app, default_limits=["100/day"])

@app.route("/api")
@limiter.limit("10/minute")
def api():
    return "rate limited"
```

### Bypass Techniques
```
X-Forwarded-For spoofing
IP rotation
Endpoint variation
```

## OWASP API Top 10
```
1. BOLA
2. Broken Auth
3. Broken Object Property
4. Unrestricted Access
5. Function Level Access
6. Mass Assignment
7. Server-Side Request Forgery
8. Security Misconfiguration
9. Improper Inventory
10. Unsafe Consumption
```

## Security Headers

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'none'
Strict-Transport-Security: max-age=31536000
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
```

## Testing Tools

### Automated
```bash
# OWASP ZAP
# Burp Suite
# Nuclei
nuclei -t api-vulns.yaml -u https://api.target.com
```

### Manual
```bash
# curl basics
curl -X GET https://api.example.com/users
curl -X POST -d '{"name":"test"}' https://api.example.com/users
curl -H "Authorization: Bearer token" https://api.example.com/users
```

## Input Validation

### Always Validate
```python
def validate_input(data):
    if 'email' in data:
        if not re.match(r'[^@]+@[^@]+\.[^@]+', data['email']):
            raise ValidationError('Invalid email')
    return True
```

## Documentation

### API Security Checklist
```
[ ] Authentication required
[ ] Authorization enforced
[ ] Rate limiting
[ ] Input validation
[ ] Output encoding
[ ] Logging/monitoring
[ ] SSL/TLS
[ ] CORS configured
```

## Tools
```
Postman - API testing
Insomnia - API testing
HTTPie - CLI tool
Swagger/OpenAPI - Documentation
```

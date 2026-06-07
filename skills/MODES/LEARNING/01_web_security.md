# LEARNING Skill: Web Security Fundamentals

## Purpose
Learn foundational web security concepts.

## OWASP Top 10
```
1. Broken Access Control
2. Cryptographic Failures
3. Injection
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable Components
7. Auth Failures
8. Data Integrity Failures
9. Logging Failures
10. SSRF
```

## HTTP Basics

### Request/Response
```
GET /path HTTP/1.1
Host: example.com
Header: value

GET /path?param=value HTTP/1.1
POST /path HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Content-Length: 27

param1=value1&param2=value2
```

### Methods
```
GET    - Retrieve resource
POST   - Submit data
PUT    - Update resource
DELETE - Remove resource
PATCH  - Partial update
HEAD   - Headers only
OPTIONS - Allowed methods
```

## SQL Injection

### Vulnerable Code
```python
# Python (vulnerable)
query = "SELECT * FROM users WHERE name='" + name + "'"
cursor.execute(query)

# PHP (vulnerable)
$query = "SELECT * FROM users WHERE name='" . $_GET['name'] . "'";
```

### Payloads
```
' OR 1=1 --
' OR 'a'='a
' UNION SELECT NULL--
admin' --
```

### Prevention
```python
# Parameterized query
query = "SELECT * FROM users WHERE name = ?"
cursor.execute(query, (name,))
```

## XSS (Cross-Site Scripting)

### Types
```
Reflected    - In URL, immediate
Stored       - Persisted, stored in DB
DOM-based    - Client-side only
```

### Payloads
```
<script>alert(1)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<a href="javascript:alert(1)">
```

### Prevention
```html
<!-- Encode output -->
&lt;script&gt; → &amp;lt;script&amp;gt;

<!-- CSP Header -->
Content-Security-Policy: script-src 'self'
```

## CSRF

### Attack Flow
```
1. User logged into site
2. User visits malicious site
3. Malicious site sends request to target
4. Browser includes cookies automatically
```

### Prevention
```html
<!-- CSRF Token -->
<input type="hidden" name="csrf_token" value="random">

<!-- SameSite Cookie -->
Set-Cookie: session=xyz; SameSite=Strict
```

## IDOR

### Vulnerable Pattern
```
/profile/123  → Shows user 123
/profile/124  → Shows user 124 (IDOR!)
```

### Prevention
```python
# Check ownership
if resource.user_id != current_user.id:
    abort(403)
```

## Security Headers

```http
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
```

## Learning Resources

### Practice Platforms
```
- PortSwigger Web Academy
- OWASP WebGoat
- DVWA
- Juice Shop
- PentesterLab
```

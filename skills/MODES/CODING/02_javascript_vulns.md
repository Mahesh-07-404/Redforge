# CODING Skill: Vulnerable JavaScript Patterns

## Purpose
Understand common vulnerable JavaScript patterns.

## Prototype Pollution

### Vulnerable
```javascript
// Merge object without check
function merge(target, source) {
  for (let key in source) {
    target[key] = source[key]; // Vulnerable!
  }
  return target;
}

// Attack
merge({}, JSON.parse('{"__proto__":{"admin":true}}'));
console.log({}.admin); // true!
```

### Secure
```javascript
function safeMerge(target, source) {
  for (let key in source) {
    if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
      continue; // Skip dangerous keys
    }
    target[key] = source[key];
  }
  return target;
}

// Or use Object.assign with filter
const safeKeys = Object.keys(source).filter(k => !['__proto__', 'constructor', 'prototype'].includes(k));
Object.assign(target, {...source});
```

## XSS (Cross-Site Scripting)

### Vulnerable
```javascript
// Direct HTML insertion
document.getElementById('output').innerHTML = userInput;

// URL parameters
const name = new URLSearchParams(location.search).get('name');
document.write(`Hello ${name}`);
```

### Secure
```javascript
// Use textContent
document.getElementById('output').textContent = userInput;

// Escape HTML
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Or use DOMPurify
const clean = DOMPurify.sanitize(userInput);
```

## Code Injection

### Vulnerable
```javascript
// eval
eval(userCode);

// Function constructor
const fn = new Function(userCode);
fn();

// setTimeout/setInterval with string
setTimeout(userCode, 1000);
```

### Secure
```javascript
// Never use eval with user input
// Use JSON.parse for data
const data = JSON.parse(userJson);

// For dynamic code, use sandboxed iframes
// Or Web Workers
const worker = new Worker('worker.js');
```

## Path Traversal

### Vulnerable
```javascript
const path = require('path');
const fs = require('fs');

const filename = req.query.file;
const filepath = path.join('/var/www/uploads', filename);
fs.readFile(filepath);
```

### Secure
```javascript
const path = require('path');

function safeFilePath(baseDir, userPath) {
  const resolved = path.resolve(baseDir, userPath);
  if (!resolved.startsWith(baseDir)) {
    throw new Error('Path traversal detected');
  }
  return resolved;
}

const filepath = safeFilePath('/var/www/uploads', req.query.file);
fs.readFile(filepath);
```

## Regex DoS (ReDoS)

### Vulnerable
```javascript
// Catastrophic backtracking
const regex = /^(a+)+$/;
const input = 'aaaa' + 'a'.repeat(20); // Causes exponential time
```

### Secure
```javascript
// Use atomic groups or possessive quantifiers
const regex = /^(a+)+$/; // Rewrite as:
const safeRegex = /^a(?:aa)*$/;

// Or use simpler patterns
const safeRegex = /^a{1,100}$/;
```

## SQL Injection (Node.js)

### Vulnerable
```javascript
// String concatenation
const query = "SELECT * FROM users WHERE name='" + name + "'";
db.query(query);

// Template literals
const query = `SELECT * FROM users WHERE name='${name}'`;
```

### Secure
```javascript
// Parameterized queries
const query = 'SELECT * FROM users WHERE name = ?';
db.query(query, [name]);

// Named parameters
const query = 'SELECT * FROM users WHERE name = :name';
db.query(query, { name: name });
```

## JWT Vulnerabilities

### Vulnerable
```javascript
// Algorithm none
jwt.verify(token, '', { algorithms: ['none'] });

// Weak secret
jwt.verify(token, 'secret123');

// No expiration check
jwt.verify(token, secret);
```

### Secure
```javascript
// Specify allowed algorithms
jwt.verify(token, secret, { algorithms: ['HS256'] });

// Check expiration
jwt.verify(token, secret, { algorithms: ['HS256'], complete: true });
// Check: payload.exp > Date.now()

// Use RS256 with public key
jwt.verify(token, publicKey, { algorithms: ['RS256'] });
```

## Insecure Dependencies

### Check
```bash
# Audit dependencies
npm audit

# Check for known vulnerabilities
npm audit --audit-level=high

# Use lockfiles
npm ci  # Exact versions
```

### Package.json
```json
{
  "engines": {
    "node": ">=18.0.0"
  },
  "scripts": {
    "preinstall": "npx audit-ci --critical"
  }
}
```

## Command Injection

### Vulnerable
```javascript
const { exec } = require('child_process');
exec('ls ' + userInput);
```

### Secure
```javascript
const { execFile } = require('child_process');

// Use array form
execFile('ls', ['-la', userInput], (error, stdout) => {});

// Validate input strictly
const allowedArgs = /^[a-zA-Z0-9_-]+$/;
if (!allowedArgs.test(userInput)) {
  throw new Error('Invalid input');
}
```

## Server-Side Request Forgery (SSRF)

### Vulnerable
```javascript
const fetch = require('node-fetch');

// User controls URL
fetch(userUrl).then(r => r.text());
```

### Secure
```javascript
const allowedHosts = ['api.trusted.com', 'cdn.example.com'];
const allowedProtocols = ['https:'];

function isSafeUrl(url) {
  try {
    const parsed = new URL(url);
    return allowedHosts.includes(parsed.hostname) && 
           allowedProtocols.includes(parsed.protocol);
  } catch {
    return false;
  }
}

if (isSafeUrl(userUrl)) {
  fetch(userUrl);
}
```

## Information Disclosure

### Bad
```javascript
// Stack traces in production
app.use((err, req, res, next) => {
  res.status(500).send(err.stack);
});

// Detailed errors
res.json({ error: err.message, stack: err.stack });
```

### Good
```javascript
const isProduction = process.env.NODE_ENV === 'production';

app.use((err, req, res, next) => {
  if (isProduction) {
    res.status(500).send('Internal Server Error');
    console.error(err);
  } else {
    res.status(500).send(err.stack);
  }
});
```

## Hardcoded Secrets

### Bad
```javascript
const API_KEY = 'sk_live_1234567890';
const DB_PASSWORD = 'secret123';
```

### Good
```javascript
// Environment variables
const API_KEY = process.env.API_KEY;
const DB_PASSWORD = process.env.DB_PASSWORD;

// Validate at startup
if (!API_KEY) {
  throw new Error('API_KEY not configured');
}
```

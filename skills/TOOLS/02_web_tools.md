# TOOLS Skill: Web Application Tools

## Purpose
Master web application testing tools.

## Proxy Tools

### Burp Suite
```bash
# Start Burp
burpsuite &

# Proxy settings
# Browser: {target}:8080
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
zap-cli quick-scan https://{target}
zap-cli spider https://{target}
zap-cli active-scan https://{target}
```

## Fuzzing

### ffuf
```bash
# Basic fuzzing
ffuf -w wordlist.txt -u https://{target}/FUZZ

# POST fuzzing
ffuf -w wordlist.txt -u https://{target}/login -X POST -d "user=admin&pass=FUZZ"

# Headers
ffuf -w wordlist.txt -u https://{target}/ -H "X-Forwarded-By: FUZZ"

# Virtual host
ffuf -w wordlist.txt -u https://{target} -H "Host: FUZZ.{target}"

# Rate limiting
ffuf -w wordlist.txt -u https://{target}/FUZZ -t 10 -p 0.1

# Colors
ffuf -w wordlist.txt -u https://{target}/FUZZ -c
```

### wfuzz
```bash
wfuzz -w wordlist.txt https://{target}/FUZZ
wfuzz -w wordlist.txt -d "user=admin&pass=FUZZ" https://{target}/login
```

### gobuster
```bash
# Directory busting
gobuster dir -u https://{target} -w wordlist.txt

# DNS
gobuster dns -d {target} -w wordlist.txt

# Virtual hosts
gobuster vhost -u https://{target} -w wordlist.txt
```

## SQL Injection

### sqlmap
```bash
# Basic scan
sqlmap -u "https://{target}/page?id=1"

# POST request
sqlmap -u "https://{target}/login" --data="user=admin&pass=test"

# With cookie
sqlmap -u "https://{target}/page?id=1" --cookie="PHPSESSID=abc"

# List databases
sqlmap -u "https://{target}/page?id=1" --dbs

# Dump table
sqlmap -u "https://{target}/page?id=1" -D dbname -T users --dump

# Full automation
sqlmap -u "https://{target}/page?id=1" --batch --risk=3 --level=5
```

## XSS

### dalfox
```bash
# Basic scan
dalfox url https://{target}/search?q=test

# With cookies
dalfox url https://{target}/page?id=1 --cookie="PHPSESSID=abc"

# Blind XSS
dalfox url https://{target}/contact -b https://your.xss.ht
```

### xsstrike
```bash
python3 xsstrike.py -u "https://{target}/search?q=test"
```

## Command Injection

### commix
```bash
# Basic
commix -u "https://{target}/ping?ip={target}"

# POST data
commix -u "https://{target}/ping" --data="ip={target}"
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
http GET https://api.{target}/users

# With auth
http GET https://api.{target}/protected Authorization:"Bearer token"

# POST
http POST https://api.{target}/users name="John" email="john@{target}"
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
nikto -h https://{target}
nikto -h https://{target} -p 80,443
nikto -h https://{target} -o results.txt
```

### nuclei
```bash
# Template scanning
nuclei -u https://{target}

# Specific templates
nuclei -u https://{target} -t cves/

# Custom wordlist
nuclei -u https://{target} -w wordlist.txt
```

## Content Discovery

### gau
```bash
# Get all URLs
echo {target} | gau

# With threads
gau -t 10 {target}
```

### waybackurls
```bash
echo {target} | waybackurls
```

## Javascript Analysis

### linkfinder
```bash
python3 linkfinder.py -i https://{target}/js/app.js -o results.html
```

### retire.js
```bash
# Scan JS files
retire {target}/js/app.js
retire --path {target} --jsout results.json
```

## Common Workflows

### Directory Discovery
```bash
# 1. ffuf for directories
ffuf -w /usr/share/wordlists/dirb/common.txt -u https://{target}/FUZZ

# 2. Check for backup files
ffuf -w /usr/share/wordlists/raft-small-directories.txt -u https://{target}/FUZZ.txt

# 3. Parameter discovery
ffuf -w params.txt -u https://{target}/page?FUZZ=value
```

### Full Web Assessment
```bash
# 1. Nikto scan
nikto -h https://{target} -o nikto.txt

# 2. Nuclei scan
nuclei -u https://{target} -o nuclei.txt

# 3. ZAP scan
zap-cli quick-scan https://{target}

# 4. Manual testing with Burp
```

## RedForge Integration
```
Use these tools within RedForge modes:
- bugbounty: Active reconnaissance
- ctf: Web challenges
- learning: Practice web security
```

## TOOL EXECUTION & ANTI-HALLUCINATION RULES
- **No Simulation**: You are strictly forbidden from simulating execution, mocking outputs, or pretending tool execution occurred. Only actual console output returned from a `TOOL:` block execution may be interpreted.
- **Target Binding**: All command arguments, parameters, and targets must be dynamically bound to the active session target `{target}`. Never replace the user target with a dummy placeholder (e.g. `example.com`).
- **No Evidence, No Finding**: If the tool command does not return output confirming a port, service, or vulnerability, do not report it as discovered.

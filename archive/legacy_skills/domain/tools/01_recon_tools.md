# TOOLS Skill: Reconnaissance Tools

## Purpose
Master reconnaissance tools for RedForge.

## Network Scanning

### nmap
```bash
# Basic scan
nmap {target}

# Port scan
nmap -p- {target}              # All ports
nmap -p 80,443 {target}        # Specific ports
nmap -sV {target}              # Version detection
nmap -sC {target}              # Default scripts

# Aggressive scan
nmap -A {target}               # OS, version, scripts, traceroute

# Timing (T0-T5)
nmap -T4 {target}              # Fast

# Output
nmap -oA results {target}      # All formats
nmap -oN results.nmap {target} # Normal
```

### masscan
```bash
# Faster than nmap
masscan -p1-65535 {target} --rate=10000

# Use specific interface
masscan -p1-1000 10.0.0.0/24 --adapter=eth0
```

## DNS Enumeration

### dig
```bash
dig {target} A
dig {target} MX
dig {target} TXT
dig {target} NS
dig {target} ANY
dig @dns.server {target} AXFR
```

### dnsenum
```bash
dnsenum {target}
dnsenum -f wordlist.txt {target}
```

### fierce
```bash
fierce -dns {target}
fierce -dnsserver dns.server {target}
```

### subfinder
```bash
subfinder -d {target}
subfinder -d {target} -o subdomains.txt
```

### amass
```bash
amass enum -passive -d {target}
amass enum -active -d {target}
amass enum -brute -d {target}
```

## Subdomain Bruteforce

### ffuf
```bash
ffuf -w wordlist.txt -u https://FUZZ.{target}
ffuf -w wordlist.txt -u https://{target} -H "Host: FUZZ.{target}"

# Recursive
ffuf -w wordlist.txt -u https://{target}/FUZZ -recursion
```

### gobuster
```bash
gobuster dns -d {target} -w wordlist.txt
gobuster vhost -u https://{target} -w wordlist.txt
```

## Web Recon

### dirb
```bash
dirb http://{target}
dirb http://{target} /usr/share/dirb/wordlists/small.txt
```

### dirbuster
```bash
# GUI alternative
```

### whatweb
```bash
whatweb {target}
whatweb -a 4 {target}  # Aggressive
```

### wafw00f
```bash
wafw00f https://{target}
```

## SSL Analysis

### sslscan
```bash
sslscan {target}:443
sslscan --show-certificate {target}
```

### testssl
```bash
testssl {target}:443
testssl --json-pretty {target}
```

### openssl
```bash
openssl s_client -connect {target}:443
openssl s_client -connect {target}:443 -showcerts
openssl s_client -connect {target}:443 -servername {target}
```

## OSINT Tools

### theHarvester
```bash
theHarvester -d {target} -b all
theHarvester -d {target} -b google,linkedin
```

### sherlock
```bash
python3 sherlock username
```

### maltego
```bash
# GUI application
# Community edition available
```

### recon-ng
```bash
recon-ng
[recon-ng] > workspaces create pentest
[recon-ng] > db insert companies
[recon-ng] > modules load
```

## Traffic Analysis

### mitmproxy
```bash
mitmproxy -p 8080
mitmweb  # Web UI
mitmdump  # Non-interactive
```

### Burp Suite
```bash
# Start Burp
# Configure browser proxy
# Use Spider, Scanner, Intruder
```

## Automation

### AutoRecon
```bash
python3 autorecon.py {target}
```

### nmapAutomator
```bash
./nmapAutomator.sh {target} All
```

## RedForge Integration

### Tool Detection
```bash
# RedForge auto-detects tools
# Manual check:
which nmap
which ffuf
which sqlmap
```

### Tool Installation
```bash
# RedForge can install missing tools
redforge install nmap
redforge install ffuf
```

## Usage Examples

### Basic Recon
```bash
# 1. Nmap scan
nmap -sV -sC -oA nmap_results {target}

# 2. Subdomain enumeration
subfinder -d {target} -o subdomains.txt

# 3. Directory busting
ffuf -w wordlist.txt -u https://{target}/FUZZ

# 4. SSL analysis
sslscan {target}
```

### Full Port Scan
```bash
nmap -p- -sV -A -oA full_scan {target}
masscan -p1-65535 {target} --rate=10000
```

## Tips
```
- Start with passive recon
- Use multiple tools for completeness
- Save all output
- Correlate results
```

## TOOL EXECUTION & ANTI-HALLUCINATION RULES
- **No Simulation**: You are strictly forbidden from simulating execution, mocking outputs, or pretending tool execution occurred. Only actual console output returned from a `TOOL:` block execution may be interpreted.
- **Target Binding**: All command arguments, parameters, and targets must be dynamically bound to the active session target `{target}`. Never replace the user target with a dummy placeholder (e.g. `example.com`).
- **No Evidence, No Finding**: If the tool command does not return output confirming a port, service, or vulnerability, do not report it as discovered.

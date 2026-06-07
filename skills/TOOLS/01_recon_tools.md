# TOOLS Skill: Reconnaissance Tools

## Purpose
Master reconnaissance tools for RedForge.

## Network Scanning

### nmap
```bash
# Basic scan
nmap target.com

# Port scan
nmap -p- target.com              # All ports
nmap -p 80,443 target.com        # Specific ports
nmap -sV target.com              # Version detection
nmap -sC target.com              # Default scripts

# Aggressive scan
nmap -A target.com               # OS, version, scripts, traceroute

# Timing (T0-T5)
nmap -T4 target.com              # Fast

# Output
nmap -oA results target.com      # All formats
nmap -oN results.nmap target.com # Normal
```

### masscan
```bash
# Faster than nmap
masscan -p1-65535 target.com --rate=10000

# Use specific interface
masscan -p1-1000 10.0.0.0/24 --adapter=eth0
```

## DNS Enumeration

### dig
```bash
dig target.com A
dig target.com MX
dig target.com TXT
dig target.com NS
dig target.com ANY
dig @dns.server target.com AXFR
```

### dnsenum
```bash
dnsenum target.com
dnsenum -f wordlist.txt target.com
```

### fierce
```bash
fierce -dns target.com
fierce -dnsserver dns.server target.com
```

### subfinder
```bash
subfinder -d target.com
subfinder -d target.com -o subdomains.txt
```

### amass
```bash
amass enum -passive -d target.com
amass enum -active -d target.com
amass enum -brute -d target.com
```

## Subdomain Bruteforce

### ffuf
```bash
ffuf -w wordlist.txt -u https://FUZZ.target.com
ffuf -w wordlist.txt -u https://target.com -H "Host: FUZZ.target.com"

# Recursive
ffuf -w wordlist.txt -u https://target.com/FUZZ -recursion
```

### gobuster
```bash
gobuster dns -d target.com -w wordlist.txt
gobuster vhost -u https://target.com -w wordlist.txt
```

## Web Recon

### dirb
```bash
dirb http://target.com
dirb http://target.com /usr/share/dirb/wordlists/small.txt
```

### dirbuster
```bash
# GUI alternative
```

### whatweb
```bash
whatweb target.com
whatweb -a 4 target.com  # Aggressive
```

### wafw00f
```bash
wafw00f https://target.com
```

## SSL Analysis

### sslscan
```bash
sslscan target.com:443
sslscan --show-certificate target.com
```

### testssl
```bash
testssl target.com:443
testssl --json-pretty target.com
```

### openssl
```bash
openssl s_client -connect target.com:443
openssl s_client -connect target.com:443 -showcerts
openssl s_client -connect target.com:443 -servername target.com
```

## OSINT Tools

### theHarvester
```bash
theHarvester -d target.com -b all
theHarvester -d target.com -b google,linkedin
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
python3 autorecon.py target.com
```

### nmapAutomator
```bash
./nmapAutomator.sh target.com All
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
nmap -sV -sC -oA nmap_results target.com

# 2. Subdomain enumeration
subfinder -d target.com -o subdomains.txt

# 3. Directory busting
ffuf -w wordlist.txt -u https://target.com/FUZZ

# 4. SSL analysis
sslscan target.com
```

### Full Port Scan
```bash
nmap -p- -sV -A -oA full_scan target.com
masscan -p1-65535 target.com --rate=10000
```

## Tips
```
- Start with passive recon
- Use multiple tools for completeness
- Save all output
- Correlate results
```

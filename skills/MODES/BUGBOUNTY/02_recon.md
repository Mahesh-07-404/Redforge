# Reconnaissance Techniques

## Passive Recon

### DNS Enumeration
```bash
# WHOIS lookup
whois example.com

# DNS records
dig example.com ANY
dig +short MX example.com
dig +short TXT example.com

# Subdomain enumeration
subfinder -d example.com
amass enum -passive -d example.com

# Certificate transparency
curl -s "https://crt.sh/?q=%.example.com&output=json"
```

### OSINT
```bash
# Google dorking
site:example.com
site:example.com filetype:pdf
site:example.com intitle:"admin"

# Technology detection
wappalyzer https://example.com
whatweb https://example.com
```

## Active Recon

### Port Scanning
```bash
# Quick scan
nmap -sV --top-ports 20 -T4 target.com

# Full scan
nmap -sV -p- -T4 target.com

# UDP scan
nmap -sU --top-ports 20 target.com
```

### Service Discovery
```bash
# Service version detection
nmap -sV target.com

# Default credential checking
nmap --script default-accounts target.com
```

## Recon Automation

```python
def full_recon(target):
    results = {}
    results["whois"] = run_whois(target)
    results["dns"] = enumerate_dns(target)
    results["subdomains"] = enumerate_subdomains(target)
    results["ports"] = scan_ports(target)
    results["tech"] = detect_technologies(target)
    return results
```

## Recon Checklist

- [ ] WHOIS information
- [ ] DNS records
- [ ] Subdomains
- [ ] IP ranges
- [ ] Email addresses
- [ ] Technology stack
- [ ] Open ports
- [ ] Service versions

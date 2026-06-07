# Subdomain Enumeration

## Enumeration Methods

### 1. Brute Force
```bash
# With ffuf
ffuf -w wordlist.txt -u https://FUZZ.example.com

# With gobuster
gobuster dns -d example.com -w wordlists/subdomains.txt
```

### 2. OSINT Sources
```bash
# Certificate Transparency
curl -s "https://crt.sh/?q=example.com&output=json"
amass enum -passive -d example.com

# VirusTotal
curl -s "https://www.virustotal.com/api/v3/domains/example.com/subdomains"

# Shodan
shodan domain example.com
```

### 3. DNS Brute Force
```bash
# With massdns
massdns -r resolvers.txt -t A names.txt -o S

# With shuffledns
shuffledns -d example.com -w wordlist.txt -r resolvers.txt
```

## Tools

| Tool | Type | Speed |
|------|------|-------|
| subfinder | Passive | Fast |
| amass | Passive | Medium |
| ffuf | Active | Fast |
| gobuster | Active | Medium |
| shuffledns | Active | Fast |

## Wordlists

### Common Subdomains
```
www, api, mail, ftp, localhost, webmail, smtp
pop, ns, mysql, forum, news, vpn, cdn
cloud, staging, dev, test, admin, store
```

## Validation

```bash
# Verify subdomains are live
for sub in $(cat subs.txt); do
    if host "$sub.example.com" | grep "has address" > /dev/null; then
        echo "$sub.example.com"
    fi
done
```

## Automation

```python
def enumerate_subdomains(domain):
    subdomains = set()
    
    # Passive sources
    subdomains |= crt_sh(domain)
    subdomains |= virustotal(domain)
    subdomains |= amass(domain)
    
    # Active bruteforce
    subdomains |= ffuf_bruteforce(domain)
    
    # Validation
    subdomains = validate_alive(subdomains)
    
    return subdomains
```

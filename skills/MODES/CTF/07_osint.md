# CTF Skill: OSINT (Open Source Intelligence)

## Purpose
Gather information using publicly available sources for CTF challenges.

## Email Analysis

### Email Header Parsing
```python
import email
from email.header import decode_header

def parse_email_header(header):
    msg = email.message_from_string(header)
    for key, value in msg.items():
        decoded = decode_header(value)
        print(f"{key}: {decoded}")
```

### Email Lookup
```
https://hunter.io/ - Email hunter
https://haveibeenpwned.com/ - Breach database
https://emailrep.io/ - Email reputation
```

## Domain Research

### DNS Lookup
```bash
# DNS records
dig domain.com ANY
dig domain.com A
dig domain.com MX
dig domain.com TXT

# Zone transfer
dig axfr domain.com @dns.server

# Online tools
# ViewDNS.info
# DNSdumpster.com
# SecurityTrails.com
```

### WHOIS
```bash
whois domain.com
whois -h whois.verisign.com "=domain.com"
```

### Subdomain Discovery
```bash
# Passive enumeration
amass enum -passive -d domain.com
subfinder -d domain.com
assetfinder domain.com

# Brute force
ffuf -w wordlist.txt -u https://FUZZ.domain.com
```

## Social Media OSINT

### Twitter
```
- Advanced search operators
- geolocation filtering
- profile analysis
- follower relationships
```

### LinkedIn
```
- Company employees
- Job titles
- Email patterns
```

### GitHub
```bash
# Search repositories
site:github.com "keyword"

# User enumeration
https://github.com/USERNAME

# Gist search
https://gist.github.com/search

# Commit history
git log --all --source --remotes
```

## Image Analysis

### Metadata Extraction
```bash
exiftool image.jpg
exiftool -a -u -g1 image.jpg  # All metadata

# Remove/edit metadata
exiftool -all= image.jpg
```

### Reverse Image Search
```
https://images.google.com
https://tineye.com
https://yandex.com/images/
```

### Geolocation
```bash
# Check landmarks
# Weather patterns
# Shadows (suncalc.js)
# License plates
# Street signs
```

## People Search

### Public Records
```
- pipl.com
- beenverified.com
- spokeo.com
- whitepages.com
```

### Business Records
```
- corporationwiki.com
- opencorporates.com
- sunbiz.org (Florida)
```

## Password Leak Search
```bash
# HaveIBeenPwned API
curl -s "https://api.pwnedpasswords.com/range/$(echo -n password | sha1 | cut -c1-5)" | grep $(echo -n password | sha1 | cut -c6-40 | tr '[:lower:]' '[:upper:]')
```

## Network Analysis

### WiFi Research
```bash
# Find WPS networks
wash -i wlan0mon

# Crack WPA
hashcat -m 2500 handshake.hccapx wordlist.txt

# Lookup router info
https://wigle.net/
```

## Metadata Patterns

### Common Metadata
```
Camera: Make, Model, Serial
GPS: Latitude, Longitude
Software: Editing tools
Author: Username, Email
```

### Geolocation from Metadata
```
https://metasp把握utal.com/
https://imgops.com/
```

## CTF-Specific OSINT

### Flag Patterns
```
flag{...}
FLAG{...}
pctf{...}
[program_prefix]{...}
```

### Hidden Information
```bash
# Check for hidden text
strings image.png | grep -i flag

# LSBR steganography
# Hiden in least significant bits

# Check for zsteg patterns
zsteg image.png -a
```

## Useful Search Engines
```
- Google (advanced operators)
- Bing
- DuckDuckGo
- Shodan (IoT devices)
- Censys (certificates)
- Hunter.io (emails)
- LeakIX (data leaks)
```

## Google Dorking
```
site:target.com filetype:pdf
site:target.com intitle:"admin"
site:target.com inurl:login
site:target.com filetype:sql
site:target.com "password"
site:target.com "flag{"
inurl:admin filetype:xlsx
intitle:"index of" "backup"
```

## API Research
```bash
# Find API endpoints
site:api.target.com
site:target.com/api
site:github.com target

# Check documentation
/swagger
/api-docs
/api/v1
/api/v2
```

## Password Patterns
```bash
# Common CTF passwords
rockyou.txt
darkweb2017-top10000.txt

# Targeted wordlists
# Use cewl to generate
cewl https://target.com -w wordlist.txt
```

## Checklist
```
[ ] WHOIS lookup
[ ] DNS records
[ ] Subdomain enumeration
[ ] Social media search
[ ] Image metadata
[ ] Document metadata
[ ] Code repository search
[ ] Leak database search
[ ] Google dorking
[ ] Archive.org (Wayback)
```

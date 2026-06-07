# CTF Skill: Network Traffic Analysis

## Purpose
Advanced network forensics and analysis.

## PCAP Analysis

### Basic Analysis
```bash
# List packets
tcpdump -r capture.pcap

# Filter by protocol
tcpdump -r capture.pcap 'tcp'
tcpdump -r capture.pcap 'udp port 53'
tcpdump -r capture.pcap 'icmp'

# HTTP traffic
tcpdump -r capture.pcap 'tcp port 80 and http'
```

### tshark
```bash
# Extract fields
tshark -r capture.pcap -Y 'http' -T fields -e http.request.method -e http.request.uri

# Extract all URLs
tshark -r capture.pcap -Y 'http.request' -T fields -e http.request.full_uri

# DNS queries
tshark -r capture.pcap -Y 'dns.qry.name' -T fields -e dns.qry.name

# HTTP POST data
tshark -r capture.pcap -Y 'http.request.method == POST' -T fields -e http.file
```

## Extracting Files

### HTTP Objects
```bash
# Extract from pcap
chaosreader capture.pcap

# Or use pcap处理好
for pkt in packets:
    if pkt.haslayer(Raw):
        data = pkt[Raw].load
        if b'HTTP' in data:
            # Check for file content
```

### Reconstruct Streams
```python
from scapy.all import *

def extract_streams(pcap):
    streams = {}
    packets = rdpcap(pcap)
    
    for pkt in packets:
        if pkt.haslayer(TCP):
            key = (pkt[IP].src, pkt[TCP].sport, pkt[IP].dst, pkt[TCP].dport)
            if key not in streams:
                streams[key] = []
            streams[key].append(pkt)
    
    return streams
```

## Malware Analysis

### C2 Traffic
```bash
# Find suspicious connections
tshark -r capture.pcap -Y 'tcp.payload' | head -50

# Check for shell commands
tshark -r capture.pcap -Y 'tcp.port == 4444' | strings

# HTTP C2 patterns
tshark -r capture.pcap -Y 'http' -T fields -e http.host | sort | uniq
```

### Encoded Traffic
```python
# Base64 in HTTP
# XOR encoded
# Custom protocols

# Detect beaconing
# Same destination, regular intervals
```

## TLS/SSL Analysis

### Extract Certificates
```bash
# Get certificate
openssl s_client -connect host:port -showcerts </dev/null 2>/dev/null | openssl x509

# From pcap with keys
# Extract master secret
# Wireshark can decrypt
```

### TLS Patterns
```python
# JA3 fingerprinting
# Used to identify malware
# ja3 = hash(tls_client_hello)

# Tools
# ja3tools
python ja3tools.py -f capture.pcap
```

## DNS Analysis

### Tunneling Detection
```bash
# Long subdomain queries
# Random looking subdomains
# High frequency

tshark -r capture.pcap -Y 'dns' | awk '{print $8}' | cut -d. -f1 | sort | uniq -c | sort -rn | head

# Length distribution
tshark -r capture.pcap -Y 'dns.qry.name' -T fields -e dns.qry.name | awk '{print length($0)}' | sort -rn | head
```

### Data Exfiltration
```python
# Check for large DNS responses
# Look for base64 in queries
# Identify patterns

def detect_dns_tunnel(pcap):
    # Count queries per domain
    # Check entropy
    # Look for data patterns
```

## SMB Analysis

### Attacks
```bash
# EternalBlue (CVE-2017-0144)
# Check for SMBv1
# Large transaction packets

tshark -r capture.pcap -Y 'smb' | head
```

### NTML Relay
```bash
# Check for NTLM authentication
tshark -r capture.pcap -Y 'ntlmssp' | head
```

## Attack Patterns

### ARP Spoofing
```bash
# Check for ARP poisoning
tshark -r capture.pcap -Y 'arp' | awk '{print $4, $5}' | sort | uniq -c

# Unusual MAC addresses
```

### Port Scanning
```python
# Detect scan patterns
# SYN to many ports
# Connection attempts in sequence

def detect_portscan(pcap):
    src_ips = set()
    for pkt in packets:
        if pkt.haslayer(TCP) and pkt[TCP].flags & 0x02:  # SYN
            src_ips.add(pkt[IP].src)
    return src_ips
```

### Brute Force
```bash
# Multiple failed logins
tshark -r capture.pcap -Y 'http.response.code == 401' | wc -l

# Same source, many attempts
```

## Encryption

### Decrypt TLS
```bash
# Using session keys
# Export from browser: SSLKEYLOGFILE
# Load in Wireshark

# Or use mitmproxy
mitmproxy -r capture.pcap
```

### Weak Encryption
```bash
# Check for weak ciphers
# NULL cipher
# Export strength

tshark -r capture.pcap -Y 'ssl' | grep -i "cipher"
```

## Tools

### Scapy
```python
from scapy.all import *

# Load pcap
packets = rdpcap('capture.pcap')

# Analyze
for pkt in packets:
    if pkt.haslayer(DNS):
        print(pkt[DNS].qd.qname)

# Craft packets
packet = IP(dst="target")/TCP(dport=80)/"GET / HTTP/1.1\r\n\r\n"
send(packet)
```

### Forensics Tools
```bash
# tcpflow - extract streams
tcpflow -r capture.pcap

# driftnet - extract images
driftnet -i eth0

# urlsnarf - extract URLs
urlsnarf -i eth0
```

## Checklist
```
[ ] Identify protocols
[ ] Extract HTTP objects
[ ] Analyze DNS traffic
[ ] Check for encryption
[ ] Detect attacks
[ ] Find malware C2
[ ] Extract credentials
[ ] Reconstruct sessions
```

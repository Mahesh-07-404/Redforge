# LEARNING Skill: Networking Fundamentals

## Purpose
Learn networking concepts for pentesting.

## OSI Model
```
Layer 7: Application    (HTTP, FTP, DNS)
Layer 6: Presentation  (SSL, TLS)
Layer 5: Session        (NetBIOS, RPC)
Layer 4: Transport      (TCP, UDP)
Layer 3: Network        (IP, ICMP, BGP)
Layer 2: Data Link      (Ethernet, ARP)
Layer 1: Physical       (Cables, Hubs)
```

## TCP/IP Model
```
Application Layer
Transport Layer    (TCP, UDP)
Internet Layer      (IP, ICMP)
Link Layer         (Ethernet)
```

## Common Ports
```
20-21: FTP
22:   SSH
23:   Telnet
25:   SMTP
53:   DNS
80:   HTTP
443:  HTTPS
445:  SMB
3306: MySQL
3389: RDP
5432: PostgreSQL
```

## DNS

### Record Types
```
A      - IPv4 address
AAAA   - IPv6 address
CNAME  - Alias
MX     - Mail server
NS     - Nameserver
TXT    - Text/SPF
PTR    - Reverse DNS
```

### Tools
```bash
dig example.com A
dig example.com MX
dig @dns.server zone AXFR
```

## HTTP/HTTPS

### HTTP Methods
```
GET     - Retrieve
POST    - Create
PUT     - Update
DELETE  - Remove
PATCH   - Modify
HEAD    - Headers
OPTIONS - Capabilities
```

### Headers
```
Request:
GET /path HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0
Cookie: session=abc

Response:
HTTP/1.1 200 OK
Content-Type: text/html
Set-Cookie: session=xyz
```

## Subnetting

### CIDR Notation
```
/24 = 255.255.255.0 = 254 hosts
/25 = 255.255.255.128 = 126 hosts
/26 = 255.255.255.192 = 62 hosts
/27 = 255.255.255.224 = 30 hosts
```

### Private Ranges
```
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
```

## Packet Analysis

### tcpdump
```bash
tcpdump -i eth0
tcpdump -i eth0 port 80
tcpdump -i eth0 host 192.168.1.1
tcpdump -i eth0 -w output.pcap
```

### nmap
```bash
nmap -sV target        # Version scan
nmap -sC target        # Default scripts
nmap -p- target        # All ports
nmap -O target         # OS detection
```

## ARP

### ARP Cache
```bash
arp -a                  # View ARP table
arp -s IP MAC          # Static entry
arp -d IP              # Delete entry
```

## Routing

### Commands
```bash
route -n
ip route show
traceroute target
mtr target
```

## Common Attacks
```
- ARP Spoofing
- DNS Spoofing
- Man-in-the-Middle
- Port Scanning
- SYN Flood
- DNS Tunneling
```

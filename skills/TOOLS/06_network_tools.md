# TOOLS Skill: Network Analysis Tools

## Purpose
Master network analysis tools.

## Wireshark

### Installation
```bash
sudo apt install wireshark
# Or from wireshark.org
```

### Basic Usage
```bash
# Capture from interface
sudo wireshark -i eth0

# Capture to file
sudo wireshark -i eth0 -w capture.pcap

# Read capture
wireshark capture.pcap
```

### Display Filters
```bash
# HTTP only
http

# Specific IP
ip.addr == 192.168.1.1

# Source/Destination
ip.src == 192.168.1.1
ip.dst == 192.168.1.1

# Port
tcp.port == 80
udp.port == 53

# HTTP methods
http.request.method == "POST"

# Contains string
http contains "password"

# Regular expression
tcp contains "login"
```

### Follow Stream
```
Right-click packet > Follow > TCP Stream
```

### Statistics
```
Statistics > Protocol Hierarchy
Statistics > Conversations
Statistics > Endpoints
```

## tcpdump

### Installation
```bash
sudo apt install tcpdump
```

### Basic Usage
```bash
# Capture
sudo tcpdump -i eth0

# Save to file
sudo tcpdump -i eth0 -w capture.pcap

# Read file
tcpdump -r capture.pcap

# With filter
sudo tcpdump -i eth0 port 80
sudo tcpdump -i eth0 host 192.168.1.1
sudo tcpdump -i eth0 'tcp[tcpflags] & tcp-syn != 0'
```

### Filters
```bash
# Port
port 80
port 443
!port 22

# Protocol
tcp
udp
icmp

# Direction
src 192.168.1.1
dst 192.168.1.1

# Combine
tcp and port 80 and dst 192.168.1.1
```

### Advanced
```bash
# ASCII output
sudo tcpdump -i eth0 -A

# Hex and ASCII
sudo tcpdump -i eth0 -XX

# With timestamp
sudo tcpdump -i eth0 -tttt

# Snapshot length
sudo tcpdump -i eth0 -s 0  # Full packet
```

## ngrep

### Installation
```bash
sudo apt install ngrep
```

### Usage
```bash
# Basic
ngrep -i "password" port 80

# With interface
ngrep -d eth0 "login" port 443

# HTTP
ngrep -d eth0 -i "POST" "tcp and port 80"

# Save to file
ngrep -i "credit card" -o capture.pcap
```

## ettercap

### Installation
```bash
sudo apt install ettercap-graphical
```

### Usage
```bash
# GUI
ettercap -G

# Text mode
ettercap -T -i eth0 -M arp:remote /192.168.1.1// /192.168.1.2//
```

### Man-in-the-Middle
```bash
# ARP poisoning
ettercap -T -M arp /gateway// /target//

# With filter
ettercap -T -M arp:remote -F filter.ef /gateway// /target//
```

## Bettercap

### Installation
```bash
sudo apt install bettercap
# Or
go install github.com/bettercap/bettercap@latest
```

### Usage
```bash
# Interactive
sudo bettercap -iface eth0

# Commands in caplet
caplet https://example.com.cap
```

### Modules
```
net.probe    - Discover hosts
net.recon    - Reconnaissance
net.sniff    - Sniffing
net.spff     - Spoofing
arp.spoof    - ARP spoofing
dhcp6.spoof  - DHCPv6 spoofing
dns.spoof    - DNS spoofing
http.server  - HTTP server
http.proxy   - HTTP proxy
https.proxy  - HTTPS proxy
```

## scapy

### Python Usage
```python
from scapy.all import *

# Send packet
send(IP(dst="target.com")/ICMP())

# Sniff
sniff(filter="tcp port 80", count=10, prn=lambda x: x.show())

# Packet manipulation
pkt = IP(dst="target.com")/TCP(dport=80)/"GET / HTTP/1.1\r\n\r\n"
send(pkt)

# Scan
sr1(IP(dst="target.com")/ICMP())
```

### Packet Analysis
```python
# Read pcap
packets = rdpcap('capture.pcap')

# Extract URLs
for pkt in packets:
    if pkt.haslayer(Raw):
        data = pkt[Raw].load
        if b'http' in data:
            print(data)
```

## airmon-ng / airodump-ng

### Monitor Mode
```bash
# Enable monitor
sudo airmon-ng start wlan0

# Capture
sudo airodump-ng wlan0mon

# Specific channel
sudo airodump-ng wlan0mon -c 6

# Save capture
sudo airodump-ng wlan0mon -w capture -o pcap
```

## NetworkMiner

### Usage
```bash
# GUI
networkminer

# CLI
networkminer --input capture.pcap
```

## Tshark

### Usage
```bash
# Extract fields
tshark -r capture.pcap -Y http -T fields -e http.request.method -e http.request.uri

# Statistics
tshark -r capture.pcap -z io,phs

# Follow stream
tshark -r capture.pcap -z follow,tcp,ascii,0

# Export objects
tshark -r capture.pcap --export-objects http,./exported
```

## Common Workflows

### Traffic Analysis
```bash
# 1. Capture
sudo tcpdump -i eth0 -w capture.pcap

# 2. Extract HTTP
tshark -r capture.pcap -Y http -T fields -e http.request.uri > urls.txt

# 3. Extract images
tshark -r capture.pcap --export-objects http,./images

# 4. Analyze with Wireshark
wireshark capture.pcap
```

### Malware Analysis
```bash
# 1. Capture
tcpdump -i eth0 -w malware.pcap

# 2. Extract DNS
tshark -r malware.pcap -Y dns -T fields -e dns.qry.name

# 3. Find suspicious connections
tshark -r malware.pcap -Y ip.src == 192.168.1.100
```

## Tips
```
- Use filters to reduce noise
- Follow TCP streams for context
- Export objects from PCAP
- Statistics reveal patterns
- Use tshark for scripting
```

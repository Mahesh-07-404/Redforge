# CTF Skill: Forensics

## Purpose
Solve file analysis, memory forensics, and network forensics challenges.

## File Analysis

### Basic Analysis
```bash
# Identify file type
file mysterious_file

# View strings
strings mysterious_file | head -100
strings -n 8 mysterious_file  # min 8 chars

# Hex dump
xxd mysterious_file | head -50
hexdump -C mysterious_file

# Check entropy
xxd mysterious_file | ent
# Python: import math; entropy(data)
```

### File Carving
```bash
# binwalk - find embedded files
binwalk mysterious_file
binwalk -e mysterious_file  # Extract

# foremost - file recovery
foremost -i mysterious_file -o output/

# scalpel
scalpel -c scalpel.conf -i mysterious_file
```

### Steganography
```bash
# steghide (password protected)
steghide extract -sf image.jpg

# zsteg (PNG/BMP)
zsteg image.png
zsteg -E 'b1,bgr,lsb,xy' image.png

# stegsolve
java -jar stegsolve.jar

# exiftool
exiftool image.jpg

# binwalk for embedded data
binwalk -E image.jpg  # Entropy graph
```

### Image Analysis
```python
# PIL for manipulation
from PIL import Image
img = Image.open('image.png')
img.show()
img.save('output.png')

# Steganography with stepic
python3 -c "import stepic; print(stepic.decode(Image.open('image.png')))"
```

## Network Forensics

### PCAP Analysis
```bash
# Basic
tcpdump -r capture.pcap
tcpdump -r capture.pcap 'tcp port 80'

# With wireshark/tshark
tshark -r capture.pcap
tshark -r capture.pcap -Y 'http.request' -T fields -e http.request.uri

# Extract files from pcap
tcpflow -r capture.pcap
# Or
foremost -i capture.pcap -o output/
```

### Network Analysis Script
```python
from scapy.all import *

packets = rdpcap('capture.pcap')

# Extract HTTP traffic
for pkt in packets:
    if pkt.haslayer(TCP) and pkt.haslayer(Raw):
        if b'GET' in pkt[Raw].load or b'POST' in pkt[Raw].load:
            print(pkt[Raw].load)

# Extract files
for pkt in packets:
    if pkt.haslayer(Raw):
        data = pkt[Raw].load
        if b'Content-Type:' in data:
            # Extract and save
            pass
```

### DNS Analysis
```bash
# Extract DNS queries
tshark -r capture.pcap -Y 'dns' -T fields -e dns.qry.name

# Find data exfiltration via DNS
tshark -r capture.pcap -Y 'dns.qry.type == 1' | awk '{print $NF}'
```

## Memory Forensics

### Volatility
```bash
# Identify memory profile
volatility -f memory.dmp imageinfo
volatility -f memory.dmp --profile=Win10x64_19041 kdgbScan

# Common commands
volatility -f memory.dmp --profile=PROFILE pslist
volatility -f memory.dmp --profile=PROFILE netscan
volatility -f memory.dmp --profile=PROFILE cmdscan
volatility -f memory.dmp --profile=PROFILE consoles
volatility -f memory.dmp --profile=PROFILE filescan
volatility -f memory.dmp --profile=PROFILE memdump -p PID
volatility -f memory.dmp --profile=PROFILE ldrmodules
volatility -f memory.dmp --profile=PROFILE malfind
volatility -f memory.dmp --profile=PROFILE yarascan
```

### Memory Analysis
```python
# Analyze dump
strings memory.dmp | grep -i password
strings memory.dmp | grep -E 'flag\{.*\}'

# Extract binaries
volatility -f memory.dmp --profile=PROFILE dlldump -D output/
volatility -f memory.dmp --profile=PROFILE procdump -D output/
```

## Disk Forensics

### Image Mounting
```bash
# Mount image (read-only)
sudo mount -o ro,loop disk.img /mnt
sudo mount -o ro,loop,offset=32256 disk.img /mnt

# List with mmls
mmls disk.img
# Note partition offsets

# FLS for file listing
fls -o offset disk.img
```

### Registry Analysis
```bash
# Parse registry hives
regripper -r registry hives -d SYSTEM
regripper -r registry hives -d SAM

# Extract passwords
regripper -r system -h | grep -i password
```

## Log Analysis

### Common Logs
```bash
# Auth logs
/var/log/auth.log
/var/log/secure

# Syslog
/var/log/syslog

# Apache/Nginx
/var/log/apache2/access.log
/var/log/nginx/access.log

# SSH
~/.ssh/authorized_keys
/var/log/auth.log | grep sshd
```

### Timeline Analysis
```bash
# Create timeline
log2timeline.py timeline.csv memory.dmp

# Analyze with Plaso
psort.py -z UTC timeline.csv
```

## PDF Analysis
```bash
# pdfinfo
pdfinfo suspicious.pdf

# Extract streams
pdfextract suspicious.pdf

# Analyze with peepdf
peepdf -i suspicious.pdf

# Manual extraction
strings suspicious.pdf | grep -i javascript
```

## Office Documents
```bash
# oletools
olebrowse
oledump.py document.docm
oleid document.docm

# Extract macros
olevba document.docm

# Extract embedded files
officecat document.docm
```

## ZIP/JAR Analysis
```bash
# Analyze archive
zipinfo archive.zip
unzip -l archive.zip

# Crack password
fcrackzip -b -m 1 -l 1-10 -u archive.zip
john --format=zip archive.zip

# Extract hidden
binwalk archive.zip
```

## Automation Scripts
```python
#!/usr/bin/env python3
import os
import subprocess
import sys

def analyze_file(filename):
    """Basic forensics analysis"""
    print(f"[*] Analyzing: {filename}")
    
    # File type
    result = subprocess.run(['file', filename], capture_output=True, text=True)
    print(f"[+] Type: {result.stdout}")
    
    # Entropy
    with open(filename, 'rb') as f:
        data = f.read()
        entropy = 0
        for b in range(256):
            p = data.count(bytes([b])) / len(data)
            if p > 0:
                entropy -= p * (p ** 0.5)  # Simple entropy
        print(f"[+] Entropy: {entropy:.2f}")
    
    # Strings
    result = subprocess.run(['strings', '-n', '8', filename], 
                          capture_output=True, text=True)
    print(f"[+] Interesting strings:")
    for line in result.stdout.split('\n')[:20]:
        if 'flag' in line.lower() or 'password' in line.lower():
            print(f"    {line}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        analyze_file(sys.argv[1])
```

## Checklist
```
[ ] file command
[ ] Check entropy
[ ] Extract strings
[ ] Look for embedded files
[ ] Check for steganography
[ ] Analyze network traffic
[ ] Parse memory image
[ ] Mount disk images
[ ] Extract metadata
[ ] Search for flags/passwords
```

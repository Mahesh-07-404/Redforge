# TOOLS Skill: Forensics Tools

## Purpose
Master digital forensics tools.

## File Analysis

### binwalk
```bash
# Analyze file
binwalk file.bin

# Extract
binwalk -e file.bin

# Entropy graph
binwalk -E file.bin

# Signature scan
binwalk -A file.bin
```

### strings
```bash
# All strings
strings file.bin

# Min length
strings -n 8 file.bin

# With offsets
strings -t x file.bin

# Filter
strings file.bin | grep -i password
strings file.bin | grep flag
```

### exiftool
```bash
# Metadata
exiftool file.jpg

# All metadata
exiftool -a -u -g1 file.jpg

# Modify
exiftool -artist="Name" file.jpg
```

### foremost
```bash
# Carve files
foremost -i file.dd -o output/

# Specific types
foremost -t jpeg,pdf -i file.dd
```

## Memory Forensics

### volatility
```bash
# Identify profile
volatility -f memory.dmp imageinfo
volatility -f memory.dmp kdbgscan

# Common commands
volatility -f memory.dmp --profile=PROFILE pslist
volatility -f memory.dmp --profile=PROFILE netscan
volatility -f memory.dmp --profile=PROFILE cmdscan
volatility -f memory.dmp --profile=PROFILE filescan
volatility -f memory.dmp --profile=PROFILE consoles
volatility -f memory.dmp --profile=PROFILE privs
volatility -f memory.dmp --profile=PROFILE ldrmodules
volatility -f memory.dmp --profile=PROFILE malfind
volatility -f memory.dmp --profile=PROFILEyarascan
```

### Rekall (alternative)
```bash
rekall -f memory.dmp pslist
```

## Network Forensics

### tcpdump
```bash
# Capture
tcpdump -i eth0 -w capture.pcap

# Read
tcpdump -r capture.pcap

# Filter
tcpdump -r capture.pcap 'tcp port 80'
tcpdump -r capture.pcap 'host 192.168.1.1'
tcpdump -r capture.pcap 'tcp[tcpflags] == tcp-syn'
```

### tshark
```bash
# Extract fields
tshark -r capture.pcap -Y 'http' -T fields -e http.request.uri

# Statistics
tshark -r capture.pcap -z io,phs

# Follow stream
tshark -r capture.pcap -z follow,tcp,ascii,0
```

### NetworkMiner
```bash
# GUI for PCAP analysis
networkminer
```

## Disk Forensics

### mmls
```bash
# List partitions
mmls disk.img

# Show partition details
mmls -t dos disk.img
```

### fls
```bash
# List files
fls -o offset disk.img

# Deleted files
fls -d disk.img

# Recursive
fls -r disk.img
```

### icat
```bash
# Extract file by inode
icat -o offset disk.img 12345 > file.extracted
```

### sorter
```bash
# Sort files by type
sorter -f disk.img -s /tmp/sorted
```

## Image Analysis

### stegsolve
```bash
# GUI
java -jar stegsolve.jar
```

### zsteg
```bash
# PNG/BMP analysis
zsteg image.png

# Specific extraction
zsteg -E 'b1,bgr,lsb,xy' image.png > output
```

### steghide
```bash
# Extract
steghide extract -sf image.jpg

# With passphrase
steghide extract -sf image.jpg -p password
```

### exiftool
```bash
# Check metadata
exiftool image.jpg

# GPS coordinates
exiftool -GPSPosition image.jpg
```

## Log Analysis

### grep/awk/sed
```bash
# Search
grep "error" logs.txt

# Parse
awk '/error/ {print $1, $2}' logs.txt

# Replace
sed 's/old/new/g' logs.txt
```

### log2timeline
```bash
# Create timeline
log2timeline.py timeline.csv memory.dmp

# Analyze
psort.py -z UTC timeline.csv
```

## Registry Analysis

### regripper
```bash
# Extract info
regripper -r registry/SYSTEM -h
regripper -r registry/SAM -h
regripper -r registry/SOFTWARE -h
```

### volatility registry
```bash
volatility -f memory.dmp --profile=PROFILE hivelist
volatility -f memory.dmp --profile=PROFILE printkey
```

## PDF Analysis

### pdfinfo
```bash
pdfinfo suspicious.pdf
```

### peepdf
```bash
# Analyze
peepdf -i suspicious.pdf

# Commands
ppdf> stream 1
ppdf> js
```

### pdfextract
```bash
# Extract streams
pdfextract suspicious.pdf
```

## Office Documents

### oletools
```bash
# List tools
oledump.py document.docm

# Extract macros
olevba document.docm

# Analyze
oleid document.docm
```

## Password Cracking

### john
```bash
# Auto-detect
john hash.txt

# Wordlist
john --wordlist=rockyou.txt hash.txt

# Format
john --format=md5 hash.txt
```

### hashcat
```bash
# Hash types
hashcat -m 0 hash.txt wordlist.txt  # MD5
hashcat -m 1000 hash.txt wordlist.txt  # NTLM
hashcat -m 5600 hash.txt wordlist.txt  # NetNTLMv2
```

### fcrackzip
```bash
# Bruteforce
fcrackzip -b -l 1-10 -u archive.zip

# Dictionary
fcrackzip -D -p wordlist.txt archive.zip
```

## Recovery

### testdisk
```bash
# Recover partition
testdisk disk.img

# PhotoRec
photorec disk.img
```

## Automation

### AutoVol
```bash
# Automated volatility
autovol.py -f memory.dmp
```

## Common Workflows

### PCAP Analysis
```bash
# 1. Basic info
tcpdump -r capture.pcap -nn

# 2. Extract HTTP
tshark -r capture.pcap -Y 'http' -T fields -e http.request.method -e http.request.uri

# 3. Extract files
foremost -i capture.pcap -o output/

# 4. Reassemble streams
tcpflow -r capture.pcap
```

### Memory Analysis
```bash
# 1. Find profile
volatility -f memory.dmp imageinfo

# 2. Process list
volatility -f memory.dmp --profile=PROFILE pslist

# 3. Network connections
volatility -f memory.dmp --profile=PROFILE netscan

# 4. Suspicious processes
volatility -f memory.dmp --profile=PROFILE malfind
```

## Tips
```
- Save extracted data with hashes
- Maintain chain of custody
- Document all findings
- Use multiple tools for verification
```

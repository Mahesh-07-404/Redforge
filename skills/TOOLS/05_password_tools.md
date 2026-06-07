# TOOLS Skill: Password Cracking Tools

## Purpose
Master password cracking tools.

## Hashcat

### Installation
```bash
# Linux
sudo apt install hashcat

# From source
git clone https://github.com/hashcat/hashcat.git
cd hashcat && make && sudo make install
```

### Basic Usage
```bash
# Identify hash type
hashcat -m 0 --example-hashes example.dict

# Crack MD5
hashcat -m 0 hash.txt wordlist.txt

# Crack SHA256
hashcat -m 1400 hash.txt wordlist.txt

# NTML (Windows)
hashcat -m 1000 hash.txt wordlist.txt

# Show progress
hashcat -m 0 hash.txt wordlist.txt --show

# Resume session
hashcat -m 0 hash.txt wordlist.txt --restore
```

### Hash Modes
```
0    MD5
100  SHA1
1400 SHA256
1700 SHA512
1000 NTLM
5600 NetNTLMv2
5500 NetNTLMv1
7500 Kerberos
13100 Kerberos 5 TGS-REP etype 23
```

### Performance
```bash
# Benchmark
hashcat -b

# Use rules
hashcat -m 0 hash.txt wordlist.txt -r rules/best64.rule

# Mask attack
hashcat -m 0 hash.txt -a 3 ?a?a?a?a?a?a

# Hybrid attack
hashcat -m 0 hash.txt -a 6 wordlist.txt ?d?d?d
```

### Wordlists
```bash
# Common wordlists
rockyou.txt
darkc0de.txt
CrackStation.txt
SecLists/Passwords/
```

## John the Ripper

### Installation
```bash
sudo apt install john

# From source
git clone https://github.com/openwall/john.git
cd john/src && ./configure && make -j4
```

### Basic Usage
```bash
# Auto-detect
john --wordlist=rockyou.txt hashes.txt

# Specify format
john --format=md5 --wordlist=rockyou.txt hashes.txt

# Interactive mode
john hashes.txt

# Show results
john --show hashes.txt

# Format list
john --list=formats
```

### Formats
```bash
# Common formats
john --format=raw-md5 hashes.txt
john --format=raw-sha256 hashes.txt
john --format=nt hashes.txt  # NTLM
john --format=netlmv2 hashes.txt
john --format=sha512crypt hashes.txt
john --format=bcrypt hashes.txt
```

### Jumbo Features
```bash
# SSH key cracking
ssh2john.py id_rsa > ssh_hash.txt
john --wordlist=rockyou.txt ssh_hash.txt

# PDF cracking
pdf2john.py document.pdf > pdf_hash.txt
john pdf_hash.txt

# ZIP cracking
zip2john zipfile.zip > zip_hash.txt
john zip_hash.txt

# Keepass
keepass2john Database.kdbx > keepass_hash.txt
john keepass_hash.txt
```

## Hydra

### Installation
```bash
sudo apt install hydra
```

### Basic Usage
```bash
# SSH brute force
hydra -l admin -P passwords.txt ssh://target.com

# Multiple users
hydra -L users.txt -P passwords.txt ssh://target.com

# Form login
hydra target.com http-post-form "/login:user=^USER^&pass=^PASS^:Invalid" -L users.txt -P passwords.txt

# FTP
hydra -l admin -P passwords.txt ftp://target.com

# HTTP Basic Auth
hydra -l admin -P passwords.txt http-get://target.com/protected
```

### Services
```bash
# SSH
hydra -l root -P passwords.txt ssh://target.com

# FTP
hydra -l admin -P passwords.txt ftp://target.com

# SMB
hydra -l admin -P passwords.txt smb://target.com

# MySQL
hydra -l root -P passwords.txt mysql://target.com

# PostgreSQL
hydra -l postgres -P passwords.txt postgres://target.com

# HTTP forms
hydra target.com http-post-form "/login:username=^USER^&password=^PASS^:F=Invalid" -L users.txt -P passwords.txt
```

## CeWL

### Wordlist Generation
```bash
# Basic
cewl www.target.com -w wordlist.txt

# Depth
cewl www.target.com -d 3 -w wordlist.txt

# With email
cewl www.target.com -e -n -w wordlist.txt

# Minimum word length
cewl www.target.com -m 6 -w wordlist.txt
```

## Crunch

### Generate Wordlists
```bash
# Basic pattern
crunch 6 8 -o wordlist.txt  # 6-8 characters

# Specific charset
crunch 8 12 -f /usr/share/crunch/charset.lst mixalpha -o wordlist.txt

# Pattern
crunch 10 10 -t password%%@@  # password00aa-password99zz

# Combinator
crunch 4 4 -p abc  # abc, acb, bac, bca, cab, cba
```

## hashid/hashid

### Identify Hash
```bash
hashid hash.txt
# Output: 
# Analyzing: '5f4dcc3b5aa765d61d8327deb882cf99'
# [+] MD5
# [+] Domain Cached Credentials
# [+] LAN Manager
```

## wfuzz

### Web Password Attacks
```bash
# Basic auth
wfuzz -z file,passwords.txt -u https://target.com/auth -F "pwd=FUZZ"

# Form POST
wfuzz -z file,users.txt -z file,passwords.txt -d "user=FUZZ&pass=FUZ2Z" https://target.com/login

# Filter for valid responses
wfuzz -z file,passwords.txt -u https://target.com/login --hs "Invalid" -d "pass=FUZZ"
```

## Default Passwords

### Databases
```bash
# Search default credentials
# cirt.net/password
# default-passwords.com

# Common defaults
admin:admin
admin:password
root:root
root:toor
admin:1234
admin:letmein
```

## Distributed Cracking

### hashcat hashmatic
```bash
# GPU acceleration
hashcat -m 0 -D 2 hash.txt wordlist.txt  # Use GPU

# CPU only
hashcat -m 0 -D 1 hash.txt wordlist.txt
```

### Rules
```bash
# Best64
hashcat -m 0 hash.txt wordlist.txt -r rules/best64.rule

# RockYou
hashcat -m 0 hash.txt rockyou.txt -r rules/rockyou-3000.rule
```

## Tips
```
- Start with common passwords
- Use targeted wordlists
- Enable rules for variations
- GPU is much faster
- NTML is fast to crack
- bcrypt is slow by design
```

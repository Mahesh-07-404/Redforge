# CTF Mode: Overview

## Purpose
Comprehensive guide for Capture The Flag competitions.

## Categories

### Jeopardy Style
```
Web       - Web vulnerabilities
Crypto    - Cryptography challenges
Binary    - Binary exploitation
Forensics - File/memory/network analysis
PWN       - System exploitation
Misc      - Anything else
Reversing - Binary reverse engineering
OSINT     - Open source intelligence
```

### Attack/Defense
```
- Service hardening
- Patch exploitation
- Network defense
- Score server interaction
```

### King of the Hill
```
- Territory control
- Persistence maintenance
- Anti-exploitation
```

## Strategy

### Individual
1. Scan all challenges first (10 min)
2. Start with highest point value
3. Focus on familiar categories
4. Use hints wisely
5. Document progress

### Team
```
Roles:
- Lead: Coordinates, manages time
- Web: Web exploitation specialist
- Crypto: Cryptography specialist
- PWN: Binary exploitation
- Forensics: Analysis specialist
- OSINT: Intelligence gathering

Communication:
- Use team chat
- Share findings immediately
- Rotate based on progress
```

## Tools Setup

### Essential Tools
```bash
# Network
nc, nmap, netcat, tcpdump, wireshark

# Web
burpsuite, sqlmap, ffuf, dirb, curl

# Crypto
openssl, python3-pwntools, sage

# Binary
gdb, pwndbg, ropper, ROPgadget, one_gadget

# Forensics
binwalk, strings, exiftool, volatility, foremost

# Reverse
ida, ghidra, radare2, objdump
```

### Python Libraries
```bash
pip install pwntools z3-solver capstone ropper
```

## Common Flags
```
- flag{...}
- FLAG{...}
- pctf{...}
- hxp{...}
- csictf{...}
```

## Resources

### Learning Platforms
- HackTheBox
- TryHackMe
- OverTheWire
- PicoCTF
- CTFlearn
- Root.Me

### Writeup Archives
- CTFTime writeups
- YouTube channels
- GitHub writeup repos

## Time Management
```
First Hour:
1. Register and setup
2. Scan all challenges
3. Read all descriptions
4. Start 2-3 easiest

Hours 2-3:
1. Deep dive on promising challenges
2. Switch if stuck >30 min

Hours 4+:
1. Collaborate on hard challenges
2. Use hints if needed
3. Document everything for writeups
```

## Competition Types

### Online Jeopardy
- 24-48 hour duration
- Individual or team
- Async solving
- Leaderboard updates

### On-site Finals
- 6-12 hour duration
- Team based
- Physical attendance
- Live scoring

### Platform Specific
```
CTFTime events:
- Real world dates
- ICAL export
- Difficulty ratings
- Team size limits
```

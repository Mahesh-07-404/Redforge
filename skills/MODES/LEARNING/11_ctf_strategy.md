# LEARNING Skill: CTF Strategy

## Purpose
Learn effective CTF competition strategies.

## Competition Types

### Jeopardy
```
Multiple categories
Point-based scoring
Usually 24-48 hours
Individual/team
```

### Attack-Defense
```
Patch services
Exploit others
Network defense
Real-time scoring
```

### King of the Hill
```
Territory control
Persist flags
Anti-exploitation
Team coordination
```

## Jeopardy Strategy

### Time Management
```
First Hour:
- Register and setup
- Scan all challenges
- Start easy ones

Middle Hours:
- Deep dive on valuable
- Rotate based on progress

Final Hours:
- Collaborate on hard
- Use hints wisely
```

### Challenge Selection
```
1. Easy points first
2. Categories you're good at
3. Point value / difficulty ratio
4. Time to solve estimation
```

### Team Roles
```
Lead - Coordinates, manages time
Web - Web exploitation
Crypto - Cryptography
Pwn - Binary exploitation
Forensics - Analysis
OSINT - Intelligence gathering
```

## Attack-Defense

### Setup
```
Harden services
Understand architecture
Backup code
```

### Patching
```
Quick fixes
Code review
Test before deploy
```

### Offense
```
Exploit development
Automatic exploitation
Payload management
```

## Essential Tools

### Setup Script
```bash
#!/bin/bash
# Pre-competition setup

# Update tools
git pull
pip install -U pwntools z3-solver

# Copy wordlists
cp -r /opt/wordlists .

# Set aliases
alias ls='ls --color=auto'
```

### Common Commands
```bash
# Network
netcat, nmap, wireshark

# Web
burpsuite, sqlmap, ffuf

# Crypto
python3, sage, z3

# Binary
gdb, pwntools, ropper

# Forensics
binwalk, strings, volatility
```

## Documentation

### During Competition
```
Document solves
Save payloads
Note interesting techniques
```

### Writeups
```
Clear title
Reproducible steps
Impact analysis
```

## Common Mistakes

### Avoid
```
- Skipping challenge descriptions
- Not checking hints early
- Spending too long on one challenge
- Ignoring category ordering
- Forgetting to save state
- Not communicating in team
```

## Post-Competition

### After CTF
```
Read writeups
Learn unsolved challenges
Practice similar problems
Review tools and techniques
```

## Practice Resources
```
- PicoCTF (beginners)
- CTFLearn
- TryHackMe
- HackTheBox
- Root.Me
- OverTheWire
- CTF365
```

## Mental Game
```
Stay calm under pressure
Ask for help when stuck
Take breaks
Trust your skills
```

## Scoring
```
Higher points = harder challenge
First blood bonus
Team vs individual
Time-based bonuses
```

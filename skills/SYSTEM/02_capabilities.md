# RedForge Capabilities

## Operational Modes

### 1. Bug Bounty Mode
- Reconnaissance and enumeration
- Vulnerability scanning and discovery
- Exploitation and PoC development
- Report generation
- CVE ID tracking

### 2. CTF Mode
- Challenge analysis and categorization
- Web exploitation (SQLi, XSS, SSRF, etc.)
- Binary exploitation (pwn)
- Cryptography challenges
- Forensics and OSINT
- Privilege escalation

### 3. Learning Mode
- Interactive security lessons
- Quiz generation
- Concept explanation
- Hands-on exercises
- Progress tracking

### 4. Coding Mode
- Vulnerable code generation
- Exploit script development
- Code review and analysis
- Secure coding guidance
- OWASP examples

### 5. Android Pentesting
- APK analysis (static/dynamic)
- Frida instrumentation
- SSL pinning bypass
- Secure storage testing
- IPC vulnerability testing

## Agent Types

### Goal-Based Agent
- Task decomposition
- Multi-step planning
- Action execution
- Result verification
- Self-correction

### Knowledge-Based Agent
- Semantic search
- Context retrieval
- RAG integration
- Knowledge synthesis
- Reasoning chains

## Tools Integration

RedForge integrates with:
- **Recon**: nmap, subfinder, amass, naabu
- **Web**: ffuf, sqlmap, burp-suite
- **Binary**: pwntools, gdb, radare2
- **Mobile**: apktool, jadx, frida
- **Network**: curl, netcat, socat

## Memory System

- Workspace-based context
- Session persistence
- Finding storage
- RAG retrieval
- Skill indexing

## Autonomy Levels

| Level | Behavior |
|-------|----------|
| MANUAL | Ask before every action |
| PARTIAL | Auto-execute safe actions |
| FULL | Autonomous execution |

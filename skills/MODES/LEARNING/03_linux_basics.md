# LEARNING Skill: Linux Fundamentals

## Purpose
Essential Linux knowledge for security work.

## File System
```
/bin    - Essential commands
/etc    - Configuration files
/home   - User home directories
/root   - Root home directory
/tmp    - Temporary files
/var    - Variable data (logs)
/usr    - User programs
/proc   - Process information
/dev    - Device files
```

## Users & Permissions

### User Management
```bash
useradd username
userdel username
passwd username
usermod -aG sudo username

# Switch users
su - username
sudo command
```

### Permissions
```
rwx rwx rwx
421 421 421
Owner Group Others

chmod 755 file
chmod +x file
chown user:group file
```

## Processes

### Process Management
```bash
ps aux              # All processes
top                 # Interactive
htop                # Enhanced
pkill process       # Kill by name
kill PID            # Kill by ID
```

### Background/Foreground
```bash
command &           # Run in background
Ctrl+Z              # Suspend job
bg                  # Resume background
fg                  # Bring to foreground
jobs                # List jobs
```

## Networking

### Commands
```bash
ifconfig/ip addr   # Network interfaces
netstat/ss         # Connections
iptables           # Firewall
curl/wget          # HTTP clients
ping               # Connectivity
```

## Package Management

### Debian/Ubuntu
```bash
apt update
apt upgrade
apt install package
apt search package
dpkg -i package.deb
```

### Red Hat/CentOS
```bash
yum update
yum install package
dnf install package
rpm -ivh package.rpm
```

### Arch
```bash
pacman -Syu
pacman -S package
pacman -Ss pattern
```

## Text Processing

### Viewing
```bash
cat file
less file
head -n 10 file
tail -n 10 file
tail -f logfile        # Follow
```

### Searching
```bash
grep pattern file
grep -r pattern dir/
find / -name file
awk '/pattern/ {print $1}' file
sed 's/old/new/g' file
```

## Environment

### Variables
```bash
export VAR=value
echo $VAR
env
printenv
```

### PATH
```bash
echo $PATH
export PATH=$PATH:/new/dir
```

## Scripting

### Basics
```bash
#!/bin/bash

# Variables
name="value"
echo "Hello $name"

# Conditionals
if [ $var -eq 1 ]; then
    echo "one"
fi

# Loops
for i in {1..5}; do
    echo $i
done
```

## Services

### systemd
```bash
systemctl start service
systemctl stop service
systemctl restart service
systemctl status service
systemctl enable service
```

## Log Locations
```
/var/log/syslog      # System messages
/var/log/auth.log    # Authentication
/var/log/apache2/    # Apache logs
/var/log/nginx/      # Nginx logs
```

## Common Tools
```
ls, cd, pwd, mkdir, rm, cp, mv
cat, grep, sed, awk
chmod, chown, tar, gzip
ssh, scp, rsync
find, locate, which
```

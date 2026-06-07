# Port Scanning

## Quick Scan
```bash
nmap -sV --top-ports 20 -T4 target.com
```

## Full Scan
```bash
nmap -sV -p- -T4 target.com -oA full_scan
```

## Service Detection
```bash
nmap -sV target.com
# Detects versions of running services
```

## Scripts
```bash
# Default scripts
nmap -sC target.com

# Vulnerability scripts
nmap --script vuln target.com

# Specific scripts
nmap --script http-enum target.com
```

## Common Ports

| Port | Service | Notes |
|------|---------|-------|
| 21 | FTP | Anonymous access |
| 22 | SSH | Brute force |
| 23 | Telnet | Unencrypted |
| 80, 443 | HTTP/S | Web apps |
| 3306 | MySQL | Default creds |
| 5432 | PostgreSQL | Default creds |
| 6379 | Redis | No auth |
| 8080 | HTTP Alt | Proxies |

## UDP Scanning
```bash
nmap -sU --top-ports 20 target.com
```

## Automation
```python
def scan_ports(target):
    results = {}
    results["tcp"] = nmap_tcp_scan(target)
    results["udp"] = nmap_udp_scan(target)
    return results
```

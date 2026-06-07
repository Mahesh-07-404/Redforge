# Vulnerability Scanning

## Automated Scanners

### Nikto
```bash
nikto -h https://target.com
```

### Nuclei
```bash
nuclei -u https://target.com
nuclei -l urls.txt
```

### SQLMap
```bash
sqlmap -u "https://target.com/?id=1"
```

## Vulnerability Categories

### Server Vulnerabilities
- Misconfigured servers
- Outdated software
- Default credentials

### Application Vulnerabilities
- SQL Injection
- XSS
- CSRF
- IDOR

### Configuration Issues
- Missing security headers
- SSL/TLS misconfigurations
- Information disclosure

## Manual Testing Priority

1. **Critical**: SQLi, RCE, Auth bypass
2. **High**: XSS, SSRF, IDOR
3. **Medium**: CSRF, Info disclosure
4. **Low**: Missing headers, weak crypto

## Workflow

```
Scan → Identify → Verify → Prioritize → Report
```

## Custom Scans

```bash
# Specific nuclei templates
nuclei -u https://target.com -t cves/
nuclei -u https://target.com -t misconfiguration/
nuclei -u https://target.com -t technologies/
```

## False Positive Handling

1. Verify each finding manually
2. Document evidence
3. Assess real impact
4. Prioritize by severity

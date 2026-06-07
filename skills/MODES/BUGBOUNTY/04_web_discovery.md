# Web Discovery

## Crawling

### Manual Discovery
```bash
# Crawl with ffuf
ffuf -w wordlist.txt -u https://example.com/FUZZ

# Common paths
ffuf -w paths.txt -u https://example.com/FUZZ
```

### Automated Crawling
```bash
# With hakrawler
echo "https://example.com" | hakrawler

# With gospider
gospider -s https://example.com
```

## Content Discovery

### Common Endpoints
```yaml
admin: /admin, /administrator, /manage
login: /login, /signin, /auth
api: /api, /api/v1, /api/v2
files: /upload, /files, /documents
backup: /backup, /bak, /.bak
```

### Parameter Discovery
```bash
# With ffuf
ffuf -w params.txt -u https://example.com/page?FUZZ=test

# Common parameters
id, page, search, sort, filter, q, query, view
```

## Technology Fingerprinting

### Headers Analysis
```bash
curl -I https://example.com
# Look for: Server, X-Powered-By, X-Generator
```

### Source Analysis
```javascript
// Meta tags
<meta name="generator" content="WordPress 6.0">

// Script patterns
<script src="/wp-content/themes/..."></script>
```

## JavaScript Analysis

```bash
# Extract endpoints from JS
python3 -m wannabee https://example.com

# LinkFinder
linkfinder -i https://example.com/main.js -o output.html
```

## Automation

```python
def web_discovery(target):
    results = {
        "endpoints": [],
        "parameters": [],
        "technologies": [],
        "secrets": []
    }
    
    # Crawl
    results["endpoints"] = crawl(target)
    
    # Parameter fuzzing
    results["parameters"] = fuzz_params(target)
    
    # Technology detection
    results["technologies"] = detect_tech(target)
    
    return results
```

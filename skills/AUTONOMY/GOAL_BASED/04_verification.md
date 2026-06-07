# Verification and Validation

## Verification Framework

### Pre-Execution Checks
- Tool availability
- Required permissions
- Network connectivity
- Target accessibility

### Post-Execution Validation
- Output format check
- Success criteria match
- Error absence confirmation
- Data integrity

## Verification Types

### 1. Output Validation
```
Expected: "sqlmap/1.7.3#stable"
Actual: "sqlmap/1.7.3#stable" → ✓
```

### 2. State Verification
```
Before: File exists
After: File modified → ✓
```

### 3. Result Verification
```
Test: SQL injection payload
Expected: Error in response
Actual: Error present → ✓
```

### 4. Boundary Verification
```
Scope: example.com
Test: sub.example.com → ✓ In scope
Test: other.com → ✗ Out of scope
```

## Validation Patterns

### Schema Validation
```python
expected_schema = {
    "status": str,
    "data": list,
    "count": int
}
validate(output, expected_schema)
```

### Pattern Matching
```python
success_patterns = [
    r"Login successful",
    r"Welcome.*user",
    r"Token: \w+"
]
match_any(output, success_patterns)
```

### Threshold Validation
```python
if scan_duration > max_duration:
    raise TimeoutError("Scan exceeded time limit")

if memory_usage > max_memory:
    raise MemoryError("Memory limit exceeded")
```

## Verification Commands

### Health Checks
```bash
# Tool availability
which nmap

# Network reachability
ping -c 1 target.com

# Permission check
ls -la /etc/shadow
```

### Result Verification
```bash
# Check for expected output
grep "XSS" results.txt

# Count results
wc -l findings.txt

# Verify file exists
test -f poc.py && echo "PoC created"
```

## Automated Verification

```python
def verify_result(task, result):
    if not result.success:
        return False, "Task failed"
    
    if not matches_pattern(result.output, task.expected_pattern):
        return False, "Output doesn't match expected"
    
    if not within_threshold(result.duration, task.max_duration):
        return False, "Duration exceeded"
    
    return True, "Verification passed"
```

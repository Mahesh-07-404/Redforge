# Edge Case Handling

## Common Edge Cases

### 1. Empty Results
```python
if not results:
    # Log and continue
    log("No results found, trying alternative approach")
    try_alternative()
```

### 2. Partial Results
```python
if partial_results and incomplete:
    # Use what we have
    analyze(partial_results)
    log_warning("Using partial results")
```

### 3. Ambiguous Results
```python
if ambiguous_results:
    # Request clarification or use heuristics
    ask_user("Which result is correct?")
    # or apply scoring
    best = score_results(results)
```

### 4. Conflicting Results
```python
if conflicting(results):
    # Investigate further
    verify_with_alternative(results)
    # or trust most recent
    return most_recent(results)
```

### 5. Tool Discrepancies
```python
# nmap says open, curl says closed
if nmap_open and not_curl_connect():
    # nmap might be stale, verify
    verify_with_netcat()
```

## Edge Case Categories

### Network Edge Cases
- Host unreachable
- DNS resolution failure
- Rate limiting
- Connection timeout
- SSL certificate errors
- Proxy required

### Target Edge Cases
- No open ports
- All ports filtered
- WAF detected
- Honeypot detected
- Out of scope

### Tool Edge Cases
- Tool not installed
- Tool version mismatch
- Tool output format changed
- Permission denied
- Resource exhausted

### Data Edge Cases
- Binary data in output
- Non-UTF8 encoding
- Extremely large output
- Malformed responses
- Corrupted files

## Handling Strategies

### Defensive Programming
```python
try:
    result = execute()
except Exception as e:
    log(f"Unexpected error: {e}")
    return safe_default()
```

### Validation Layers
```python
# Input validation
validate(input)

# Output validation  
validate(output)

# Sanity checks
if not sanity_check(output):
    retry_or_fail()
```

### Graceful Degradation
```python
if not optimal_available():
    use_better_available()
```

## Best Practices

1. **Anticipate**: Expect edge cases
2. **Detect Early**: Catch before failure
3. **Handle Gracefully**: Don't crash
4. **Log Thoroughly**: For debugging
5. **Recover Safely**: Return to known state

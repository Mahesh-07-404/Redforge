# Failure Recovery Strategies

## Failure Categories

### 1. Recoverable Failures
Can retry and succeed:
- Network timeout
- Temporary rate limit
- Resource temporarily unavailable

### 2. Transient Failures
Can work around:
- Tool not installed (install it)
- Permission denied (escalate or skip)
- Invalid input (sanitize)

### 3. Permanent Failures
Cannot complete:
- Target down
- Out of scope
- Legal restriction

## Recovery Strategies

### Retry Strategy
```python
for attempt in range(max_retries):
    try:
        return execute()
    except RecoverableError as e:
        wait(exponential_backoff(attempt))
    except PermanentError as e:
        raise
```

### Fallback Strategy
```python
try:
    return primary_method()
except PrimaryFailed:
    return fallback_method()
except FallbackFailed:
    return emergency_method()
```

### Checkpoint Strategy
```python
save_checkpoint()
try:
    risky_operation()
except Error:
    restore_checkpoint()
    alternative_approach()
```

## Error Recovery Patterns

### Circuit Breaker
```python
breaker = CircuitBreaker(failures=5, timeout=60)

for attempt in range(max_attempts):
    try:
        result = breaker.call(tool.execute)
        return result
    except CircuitOpen:
        wait(timeout)
```

### Bulkhead
```python
# Isolate failures
pool_a = execute_in_pool("critical_tasks")
pool_b = execute_in_pool("secondary_tasks")
```

### Timeout with Fallback
```python
try:
    result = with_timeout(tool.execute, timeout=30)
except TimeoutError:
    return cached_result() or safe_default()
```

## State Recovery

### Save State
```python
state = {
    "completed": [...],
    "current": {...},
    "findings": [...]
}
save_to_disk(state)
```

### Restore State
```python
saved = load_from_disk()
if saved:
    restore_state(saved)
```

## Logging for Recovery

```python
log({
    "action": "execute_nmap",
    "args": {"target": "example.com"},
    "start_time": now(),
    "result": "failed",
    "error": "timeout",
    "retry": True
})
```

## Best Practices

1. **Fail Fast**: Detect errors early
2. **Log Everything**: For analysis and recovery
3. **Save Checkpoints**: For state recovery
4. **Exponential Backoff**: For retries
5. **Graceful Degradation**: Continue when possible

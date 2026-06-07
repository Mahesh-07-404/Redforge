# Execution Strategies

## Execution Models

### Synchronous Execution
Tasks run one at a time, in order.
```
Use when: Order matters, dependencies exist
```

### Asynchronous Execution
Tasks run in parallel.
```
Use when: Tasks are independent
```

### Hybrid Execution
Mix of sync and async.
```
Use when: Some tasks parallel, some sequential
```

## Execution Flow

```
START
  ↓
Load Context
  ↓
Generate Plan
  ↓
For Each Task:
  ├─ Check Prerequisites
  ├─ Execute Action
  ├─ Capture Output
  ├─ Verify Result
  └─ Update State
  ↓
Handle Completion
  ↓
END
```

## Tool Execution

### Command Execution
```bash
# Direct command
nmap -sV target.com

# With output capture
nmap -sV target.com -oA scan_results

# Background execution
nmap -sV target.com &

# With timeout
timeout 300 nmap -sV target.com
```

### Tool Chaining
```
Tool A output → Tool B input → Tool C output
```

### Error Handling
```python
try:
    result = execute_tool(tool, args)
except TimeoutError:
    # Handle timeout
except ToolNotFoundError:
    # Try alternative or install
except ExecutionError:
    # Log and continue
```

## Execution Best Practices

1. **Idempotency**: Safe to run multiple times
2. **Atomicity**: Complete or nothing
3. **Logging**: Record all actions
4. **Rollback**: Support undo where possible
5. **Timeout**: Set reasonable limits

## Performance Optimization

### Caching
- Cache tool results
- Reuse connections
- Store intermediate outputs

### Parallelization
- Run independent tasks together
- Use async/await patterns
- Balance load

### Resource Management
- Monitor memory usage
- Limit concurrent processes
- Clean up temporary files

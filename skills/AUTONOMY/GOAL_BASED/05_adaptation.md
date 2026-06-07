# Adaptation and Flexibility

## Adaptive Behavior

### When to Adapt
- Initial approach fails
- New information discovered
- Constraints change
- Unexpected results
- Blocked by obstacles

### Adaptation Types

#### Tool Adaptation
```
Primary tool fails → Try alternative tool
nmap fails → Try masscan
sqlmap fails → Try manual testing
```

#### Approach Adaptation
```
Passive recon fails → Active recon
Web testing fails → API testing
Authentication fails → Password spraying
```

#### Scope Adaptation
```
Subdomain not in scope → Skip
New in-scope target found → Include
```

## Decision Framework

```
Problem Detected
      ↓
Analyze Cause
      ↓
Generate Options
      ↓
Evaluate Options
      ↓
Select Best Option
      ↓
Execute and Monitor
```

## Flexibility Techniques

### 1. Fallback Chains
```python
tools = [nmap, masscan, naabu]
for tool in tools:
    try:
        return execute(tool)
    except ToolError:
        continue
```

### 2. Technique Rotation
```
Technique A (passive) fails
    ↓
Technique B (active) succeeds
    ↓
Continue with B
```

### 3. Granularity Adjustment
```
Host scan fails → Port scan
Port scan fails → Specific port check
Specific check → Manual probe
```

### 4. Timing Adaptation
```
Fast scan timeout → Slow thorough scan
Daytime blocked → Night retry
Rate limited → Backoff and retry
```

## Context Adaptation

### Based on Target
- Different OS requires different tools
- Different tech stack requires different techniques
- Different defenses require different approaches

### Based on Results
- More findings = deeper analysis
- No findings = broader scope
- Sensitive data = stop immediately

### Based on Constraints
- Time limit = prioritize high-value targets
- Rate limits = slow down requests
- Legal constraints = avoid certain tests

## Best Practices

1. **Don't Persist on Failure**: Try alternatives
2. **Log Adaptations**: Record what changed and why
3. **Update Mental Model**: Incorporate new information
4. **Know Limits**: When to stop and report
5. **Communicate Changes**: Inform user of adaptations

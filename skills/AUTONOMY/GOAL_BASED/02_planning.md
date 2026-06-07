# Planning and Execution

## Planning Framework

### Input Processing
1. Parse user request
2. Extract constraints and objectives
3. Identify available tools
4. Load relevant context

### Plan Generation
1. Break into subtasks
2. Determine tool requirements
3. Estimate complexity
4. Set checkpoints

### Execution Strategy
```
Plan → Execute Step 1 → Verify → Execute Step 2 → ... → Complete
```

## Plan Structure

### Components
```yaml
plan:
  goal: <objective>
  tasks:
    - id: 1
      action: <what to do>
      tool: <which tool>
      expected: <success criteria>
    - id: 2
      ...
  checkpoints:
    - after: 1
      verify: <what to check>
```

### Plan Types

#### Sequential
Tasks must complete in order.

#### Parallel
Independent tasks run simultaneously.

#### Adaptive
Plan adjusts based on results.

## Execution Best Practices

1. **Start Simple**: Begin with least invasive techniques
2. **Verify Progress**: Check results before proceeding
3. **Handle Failures**: Have fallback strategies
4. **Maintain Logs**: Track all actions and results
5. **Stay Focused**: Don't get distracted by tangents

## Example: Bug Bounty Plan

```yaml
goal: Find XSS in target.com
plan:
  tasks:
    - action: Reconnaissance
      tool: nmap, subfinder
      expected: List of subdomains and open ports
    
    - action: Crawl website
      tool: ffuf
      expected: List of endpoints and parameters
    
    - action: Test parameters
      tool: Manual + Burp
      expected: Identified XSS vectors
    
    - action: Verify XSS
      tool: Browser automation
      expected: Confirmed vulnerability with PoC
    
    - action: Document findings
      tool: Report generator
      expected: Complete vulnerability report
```

## Plan Adaptation

When initial plan fails:
1. Analyze failure point
2. Identify alternative approaches
3. Adjust plan
4. Continue execution

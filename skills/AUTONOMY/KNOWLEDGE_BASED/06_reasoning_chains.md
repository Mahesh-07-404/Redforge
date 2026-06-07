# Reasoning Chain Construction

## Chain Types

### 1. Deductive Reasoning
General → Specific
```
All SQL injection allows data exfiltration
This endpoint has SQL injection
Therefore: Data exfiltration is possible
```

### 2. Inductive Reasoning
Specific → General
```
SQL injection found on 3 endpoints
SQL injection likely exists on other endpoints
```

### 3. Abductive Reasoning
Observation → Best Explanation
```
SQL error observed
Best explanation: SQL injection vulnerability
```

## Chain Construction

### Basic Chain
```python
chain = [
    {"fact": "User input not sanitized", "source": "code_review"},
    {"fact": "SQL query uses user input", "source": "code_review"},
    {"fact": "Database error on input", "source": "test_result"},
    {"conclusion": "SQL injection vulnerability"}
]
```

### With Confidence
```python
chain = [
    {"fact": "Input sanitization missing", "confidence": 0.9},
    {"fact": "Query execution with input", "confidence": 0.85},
    {"fact": "Error on payload", "confidence": 0.95},
    {"conclusion": "SQL injection", "confidence": 0.9 * 0.85 * 0.95}
]
```

## Chain Validation

### Consistency Check
```python
def validate_chain(chain):
    for fact in chain:
        if contradicts_previous(fact, chain):
            return False, "Contradiction found"
    return True, "Chain valid"
```

### Completeness Check
```python
def is_complete(chain):
    required = ["evidence", "reasoning", "conclusion"]
    return all(r in chain for r in required)
```

## Chain of Thought

### Step-by-Step
```
1. Observe: Website returns database error
2. Hypothesize: SQL injection possible
3. Test: Send SQLi payload
4. Result: Error changes
5. Confirm: Injection confirmed
6. Conclude: SQL injection exists
```

### Multi-hop
```
Given: User input flows to SQL query
Given: SQL query executes
Given: Query result affects response
When: Malicious input provided
Then: Arbitrary SQL execution possible
```

## Documentation

```python
reasoning_chain = """
Chain of Reasoning for SQL Injection Finding:

1. Evidence:
   - Database error on ' OR 1=1--
   
2. Reasoning:
   - Error indicates SQL query executed
   - Input not properly sanitized
   
3. Prerequisites:
   - User-supplied input accepted
   - Input used in SQL query
   
4. Impact:
   - Data exfiltration possible
   - Authentication bypass possible
   
5. Confidence: HIGH
   - Multiple payloads tested
   - Consistent behavior
"""
```

## Best Practices

1. **Document each step**: Show the logic
2. **Include evidence**: Cite sources
3. **Check consistency**: No contradictions
4. **Acknowledge gaps**: Note missing information
5. **State confidence**: Be honest about certainty

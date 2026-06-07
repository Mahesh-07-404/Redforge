# BUGBOUNTY Skill: Business Logic Vulnerabilities

## Purpose
Identify and exploit business logic flaws that automated scanners miss.

## Framework

### 1. Authentication Flow Analysis
- Registration mechanisms
- Password reset flows
- Multi-factor authentication (MFA)
- Session management
- OAuth/OIDC flows

### 2. Financial Logic Flaws
- Price manipulation
- Currency conversion errors
- Discount/coupon abuse
- Time-based pricing gaps
- Integer overflow in monetary values

### 3. Race Conditions
- Time-of-check to time-of-use (TOCTOU)
- Concurrent coupon redemption
- Multiple account creation
- Stock quantity manipulation
- "Second-order" attacks

### 4. Workflow Bypasses
- State machine manipulation
- Skip payment steps
- Access expired trials
- Privilege escalation via workflow
- Direct object reference in transitions

### 5. IDOR Patterns
- Resource enumeration
- Horizontal privilege escalation
- Vertical privilege escalation
- Mass assignment
- API parameter tampering

### 6. Parameter Manipulation
- Client-side validation bypass
- Hidden fields exploitation
- Encoded/hashed value tampering
- JSON parameter injection
- XML parameter injection

### 7. Business Rule Testing
- Geographic restrictions bypass
- Age verification bypass
- Subscription tier exploitation
- Referral system abuse
- Loyalty points manipulation

## Testing Methodology

```
1. Map application workflow
   └─> Identify all user roles
   └─> Document all transitions

2. Enumerate all parameters
   └─> Test each for manipulation
   └─> Check for missing authorization

3. Test concurrent access
   └─> Race condition checks
   └─> TOCTOU vulnerabilities

4. Verify business rules
   └─> Boundary value analysis
   └─> Edge case exploitation
```

## Common Payloads

### Price Manipulation
```
item_price=0.01
item_price=-10
price=0
discount=9999
coupon_code=ADMINONLY
```

### Race Condition
```
# Concurrent request template
for i in {1..10}; do
  curl -X POST "$URL" [params] &
done
wait
```

### Workflow Bypass
```
# Direct state transition
POST /api/order/complete
{
  "order_id": 123,
  "status": "paid",
  "skip_payment": true
}
```

## Tools
- Burp Suite (Intruder, Repeater)
- FFUF (parameter fuzzing)
- OAuth attacks: oauth-browser
- Race conditions: Turbointruder

## Severity Guidelines
| Type | Severity | Impact |
|------|----------|--------|
| Price manipulation | Critical | Direct financial loss |
| Authentication bypass | Critical | Full account takeover |
| Race condition in payment | Critical | Free purchases |
| Workflow bypass | High | Unauthorized access |
| IDOR (sensitive data) | High | Data exposure |
| Business rule abuse | Medium | Financial impact |

## Reporting Template
```markdown
## Business Logic Vulnerability

### Summary
[One-line description of the flaw]

### Steps to Reproduce
1. [Step-by-step reproduction]
2. [Include screenshots/POC]

### Impact
[Business and security impact]

### Remediation
[Suggested fix]

### References
[Any relevant CVEs or articles]
```

## Common Bypass Techniques
- Modify POST/GET parameters
- Change HTTP methods (GET→POST)
- Remove required parameters
- Add unexpected parameters
- Use alternative encodings
- Replay valid tokens
- Bypass client-side checks

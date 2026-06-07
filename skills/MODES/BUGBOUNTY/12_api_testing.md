# API Security Testing

## API Types

### REST
```
GET /api/users
POST /api/users
GET /api/users/1
PUT /api/users/1
DELETE /api/users/1
```

### GraphQL
```
POST /graphql
query { users { id name } }
mutation { createUser(input: {...}) { id } }
```

### SOAP
```
POST /api/service.wsdl
```

## Testing Techniques

### Parameter Manipulation
```bash
# Change user ID
GET /api/users/1 → GET /api/users/2

# Add parameters
GET /api/search?q=test → GET /api/search?q=test&admin=true
```

### HTTP Methods
```bash
# Test all methods
curl -X OPTIONS http://target.com/api
curl -X PUT http://target.com/api/resource
```

### Headers
```bash
curl -H "X-Api-Key: test" http://target.com/api
curl -H "Authorization: Bearer token" http://target.com/api
```

## GraphQL Testing

### Introspection
```bash
curl -X POST http://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { types { name } } }"}'
```

### Mutation Testing
```graphql
mutation {
  login(username: "admin", password: "admin") {
    token
  }
}
```

## Common Issues

1. BOLA (Broken Object Level Authorization)
2. BFLA (Broken Function Level Authorization)
3. Mass Assignment
4. Rate Limiting
5. SSRF
6. Injection

## Tools

```bash
# Burp Suite
# OWASP ZAP
# sqlmap for API testing
# ffuf for fuzzing
```

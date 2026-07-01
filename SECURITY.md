# RedForge Security Policy & Vulnerability Disclosure

RedForge is designed for penetration testing operations and requires strict access boundaries.

---

## Security Boundaries & Rules

1. **Authentication**: All API Gateway routes are secured by default. The system supports JWT Token signing and static API Keys.
2. **Access Controls**: Role-Based Access Control (RBAC) ensures operators can only execute actions matching their assigned scopes.
3. **Safety Engine**: The Safety Engine restricts targets by validating IP addresses, domains, and ranges, preventing scan leaks into unauthorized systems.
4. **Local Binding**: The API gateway binds to `127.0.0.1:8000` by default, preventing external exposure unless explicitly overridden.

---

## Immutable Logs Verify

RedForge maintains an immutable cryptographic ledger of critical actions (logins, session additions, tool scans).
To verify the audit logs have not been retroactively altered or tampered with, run the following verification:
```python
from redforge.observability.manager import ObservabilityManager
obs = ObservabilityManager()
# Verify chain integrity
is_valid = obs.audit.verify_chain()
print(f"Log integrity verified: {is_valid}")
```

---

## Reporting Vulnerabilities

If you discover a security vulnerability in RedForge, do not open a public issue. Email details to `security@redforge.io` with a detailed proof of concept.
We will respond within 48 hours to confirm the issue and outline remediation plans.

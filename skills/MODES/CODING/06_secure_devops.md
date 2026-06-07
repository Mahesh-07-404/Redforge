# CODING Skill: Secure DevOps

## Purpose
Implement security in CI/CD pipelines.

## Pipeline Security

### GitHub Actions
```yaml
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run security scans
        run: |
          # Dependency check
          npm audit --audit-level=high
          # SAST
          semgrep --config=auto
          # DAST (in staging only)
          # Container scan
          trivy image $IMAGE
```

### GitLab CI
```yaml
security_scan:
  stage: test
  image: aquasec/trivy:latest
  script:
    - trivy fs --severity HIGH,CRITICAL .
    - trivy image --severity HIGH,CRITICAL $IMAGE
```

## Secret Management

### HashiCorp Vault
```yaml
# Don't store secrets in code
# Use Vault
- name: Fetch secrets
  uses: hashicorp/vault-action@v2
  with:
    secrets: |
      secret/data/creds username | DB_USER ;
      secret/data/creds password | DB_PASS
```

### AWS Secrets Manager
```python
import boto3
import os

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])
```

## Container Security

### Dockerfile Best Practices
```dockerfile
# Use minimal base
FROM alpine:3.18

# Don't run as root
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# No secrets in image
COPY --chown=appuser:appgroup app /app

# Health check
HEALTHCHECK --interval=30s CMD wget -qO- http://localhost:8080/health
```

### Security Scanning
```yaml
# GitHub Actions
- name: Scan container
  uses: aquasec/trivy-action@master
  with:
    image-ref: ${{ env.IMAGE }}
    format: sarif
    severity: HIGH,CRITICAL
```

## SAST (Static Analysis)

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/returntocorp/semgrep
    rev: v1.0.0
    hooks:
      - id: semgrep
        args: ['--config=auto']
  
  - repo: https://github.com/pycqa/bandit
    hooks:
      - id: bandit
```

### GitHub Action
```yaml
- name: Run Bandit
  run: |
    bandit -r ./src -f json -o bandit.json
- name: Upload Bandit results
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: bandit.json
```

## Dependency Scanning

### npm
```bash
npm audit --audit-level=high
npm outdated
npm ci --only=production
```

### Python
```bash
pip-audit
safety check
pipenv lock --keep-outdated
```

## DAST (Dynamic Analysis)

### In CI/CD
```yaml
# OWASP ZAP
- name: ZAP Scan
  uses: zaproxy/action-baseline@v0.7.0
  with:
    target: 'https://staging.example.com'
    zedt: ${{ env.ZAP_API_KEY }}
```

## Infrastructure as Code

### Terraform Security
```hcl
# Encrypted S3 bucket
resource "aws_s3_bucket" "secure" {
  bucket = "secure-bucket"
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    noncurrent_version_transition {
      days = 30
      storage_class = "GLACIER"
    }
  }
}
```

## Secrets Scanning

### GitLeaks
```yaml
- name: GitLeaks
  run: |
    gitlab-ci.yml
```

### TruffleHog
```bash
trufflehog git https://github.com/repo.git \
    --json \
    --no-update
```

## Kubernetes Security

### Security Context
```yaml
apiVersion: v1
kind: Pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10000
    fsGroup: 10000
  containers:
  - name: app
    image: app:latest
    securityContext:
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
      capabilities:
        drop:
          - ALL
```

## Monitoring

### SIEM Integration
```python
# Send security events
def log_security_event(event):
    logger.info({
        'event': event,
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'api',
        'severity': 'HIGH'
    })
```

## Supply Chain Security

### SBOM Generation
```yaml
- name: Generate SBOM
  uses: anchore/sbom-action@v0
  with:
    image: ${{ env.IMAGE }}
    format: cyclonedx-json
```

### Signed Commits
```yaml
- name: Verify commit signature
  uses: actions/verify-signatures@v2
  with:
    GITSIGN_KEY: ${{ secrets.GITSIGN_KEY }}
```

## Compliance

### Policy as Code
```rego
# OPA Rego policy
package main

deny[msg] {
    input.kind == "Deployment"
    not input.spec.securityContext.runAsNonRoot
    msg = "Containers must run as non-root"
}
```

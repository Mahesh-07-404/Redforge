# LEARNING Skill: Container Security Basics

## Purpose
Learn container security fundamentals.

## Docker Basics

### Architecture
```
Client → Docker Daemon → Containers
                    ↓
              Images, Volumes,
              Networks, Plugins
```

### Key Concepts
```
Image     - Template for containers
Container - Running instance
Volume    - Persistent data
Network   - Container communication
```

## Common Issues

### Running as Root
```dockerfile
# Bad
FROM ubuntu
CMD /bin/bash

# Good
FROM ubuntu
RUN useradd -m appuser
USER appuser
CMD /bin/bash
```

### Privileged Mode
```bash
# Dangerous - full host access
docker run --privileged image

# Use capabilities instead
docker run --cap-add=SYS_ADMIN image
```

### Sensitive Mounts
```bash
# Dangerous
docker run -v /:/host image

# Minimal needed mounts only
```

## Dockerfile Best Practices

### Base Image
```dockerfile
# Use minimal base
FROM alpine:3.18
# or
FROM scratch

# Specify versions
FROM python:3.11-slim
```

### Multi-stage Builds
```dockerfile
FROM golang:1.21 AS builder
WORKDIR /app
COPY . .
RUN go build -o app

FROM alpine:3.18
COPY --from=builder /app/app /app/
CMD ["/app/app"]
```

### Security
```dockerfile
# No secrets in image
# Use build secrets
RUN --mount=type=secret,id=aws . /root/.aws

# Update packages
RUN apt-get update && apt-get upgrade -y

# Remove unnecessary tools
RUN apt-get remove -y curl wget
```

## Scanning

### Trivy
```bash
# Scan image
trivy image nginx:latest

# Scan filesystem
trivy fs /path/to/dir

# CI integration
trivy image --exit-code 1 --severity HIGH,CRITICAL image
```

### Other Tools
```
docker-bench-security
Hadolint (Dockerfile lint)
Anchore
Snyk Container
Clair
```

## Kubernetes Security

### Pod Security
```yaml
apiVersion: v1
kind: Pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: app
    image: app:latest
    securityContext:
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
```

### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: backend
```

## Runtime Security

### Seccomp
```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "syscalls": [
    {"names": ["read", "write"], "action": "SCMP_ACT_ALLOW"}
  ]
}
```

### AppArmor/SELinux
```bash
# AppArmor profile
apparmor_parser -r profile-name < profile

# SELinux
chcon -t container_file_t /path
```

## Supply Chain Security

### Image Signing
```bash
# Docker Content Trust
export DOCKER_CONTENT_TRUST=1

# Cosign (Sigstore)
cosign sign image
cosign verify image
```

### SBOM
```bash
# Generate SBOM
syft nginx:latest -o cyclonedx-json > sbom.json

# Verify with Grype
grype sbom:sbom.json
```

## Common Vulnerabilities

### Host Kernel
```
All containers share kernel
Kernel exploits affect all containers
```

### Images
```
Outdated base images
Vulnerable packages
Secrets in layers
```

### Networking
```
Default bridge allows all traffic
No network isolation
```

## Defense in Depth
```
1. Scan images
2. Use minimal base
3. Don't run as root
4. Read-only rootfs
5. Drop capabilities
6. Network policies
7. Pod security policies
8. Runtime monitoring
```

## Tools
```
Trivy - Vulnerability scanner
Falco - Runtime security
OPA/Gatekeeper - Policy engine
Kyverno - K8s policy engine
```

## CTF Container Challenges
```
- Find secrets in images
- Escape from container
- Exploit misconfigurations
- privilege escalation
```

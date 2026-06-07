# TOOLS Skill: Container & Cloud Tools

## Purpose
Master container and cloud security tools.

## Docker Security

### Container Analysis
```bash
# Inspect container
docker inspect container_id

# View layers
docker history image_name

# Scan image
trivy image nginx:latest
docker scout cves nginx:latest

# Check for secrets
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy dockerfile:debian
```

### Docker Bench
```bash
docker run -it --net host --pid host --userns host --cap-add audit_control \
    -v /var/lib:/var/lib \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /usr/lib/systemd:/usr/lib/systemd \
    -v /etc/docker:/etc/docker \
    --label docker_bench_security \
    docker-bench-security
```

## Kubernetes Security

### kubectl Security
```bash
# Check permissions
kubectl auth can-i --list --namespace=default

# Scan pods
kubectl get pods -o json | jq '.items[].spec.containers[].securityContext'

# Check for vulnerabilities
kubectl-neat < original.yaml > cleaned.yaml
```

### kube-bench
```bash
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs job/kube-bench
```

### kube-hunter
```bash
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-hunter/main/job.yaml
kubectl logs job/kube-hunter
```

## Cloud Security Tools

### AWS

#### ScoutSuite
```bash
# Multi-cloud security scanner
python3 scoutsuite.py --provider aws

# Specific service
python3 scoutsuite.py --provider aws --services s3,ec2
```

#### Prowler
```bash
# AWS security best practices
./prowler -p aws -f us-east-1

# Specific checks
./prowler -p aws -c cislevel2
```

#### CloudSploit
```bash
# Cloud infrastructure security
cloudcsploit --export csv
```

### Azure

#### AzSK
```bash
# Azure security scanner
Get-AzSKSubscriptionSecurity

# Specific controls
Get-AzSKSubscriptionSecurity -ControlIds SVT1,SVT2
```

#### ScoutSuite Azure
```bash
python3 scoutsuite.py --provider azure
```

### GCP

#### Forseti
```bash
forseti inventory create
forseti scanner run
forseti model deploy
```

## Container Scanning

### Trivy
```bash
# Scan image
trivy image nginx:latest

# Scan filesystem
trivy fs /path/to/dir

# Scan running container
trivy container --name nginx

# Scan YAML
trivy config k8s-deployment.yaml

# Output
trivy image nginx:latest --format json -o result.json
trivy image nginx:latest --severity HIGH,CRITICAL
```

### Clair
```bash
# Local database
docker run -p 5432:5432 -e POSTGRES_PASSWORD=password arminc/clair-db:latest
docker run -p 6060:6060 --link clair-db -e DOCKER_BUCKET=postgres -e DSN="host=clair-db port=5432" arminc/clair-local-scan-service:latest

# Scan
curl -X POST -F "image=nginx:latest" http://localhost:6060/v1/scan
```

### Anchore
```bash
# Add image
anchore-cli image add nginx:latest

# Wait for analysis
anchore-cli image wait nginx:latest

# Get vulnerabilities
anchore-cli image vuln nginx:latest all
```

## Cloud Enum Tools

### Cloud_enum
```bash
# Multi-cloud enumeration
python3 cloud_enum.py -k example

# AWS
python3 cloud_enum.py -k example -l aws

# Azure
python3 cloud_enum.py -k example -l azure

# GCP
python3 cloud_enum.py -k example -l gcp
```

### S3Scanner
```bash
# Scan for open S3 buckets
python3 s3scanner.py --region us-east-1
python3 s3scanner.py -f buckets.txt
```

## Serverless Security

### Puresec
```bash
# Serverless security testing
puresec-cli scan -f serverless.yml
```

## Secrets Scanning

### Git-secrets
```bash
git secrets --install
git secrets --scan
git secrets --scan -r -- secrets.log
```

### TruffleHog
```bash
# Find secrets
trufflehog filesystem /path/to/code

# Git repo
trufflehog git https://github.com/repo.git

# S3
trufflehog s3 --bucket=bucket-name
```

## CSPM Tools

### Prisma Cloud
```bash
# Compute agentless
prisma-cloud compute scan --host <host>
```

## Checklist
```
[ ] Container image scanning
[ ] Kubernetes security audit
[ ] Cloud misconfiguration detection
[ ] Secrets detection
[ ] IAM analysis
[ ] Network security
```

# LEARNING Skill: Cloud Security Basics

## Purpose
Learn cloud security fundamentals (AWS, Azure, GCP).

## Shared Responsibility

### Provider (Security of Cloud)
```
Physical security
Network infrastructure
Hypervisor
```

### Customer (Security in Cloud)
```
Data encryption
Access control
Application security
OS patching
```

## AWS Services

### Compute
```
EC2        - Virtual servers
Lambda     - Serverless functions
ECS/EKS    - Containers
Lightsail  - Simple VMs
```

### Storage
```
S3         - Object storage
EBS        - Block storage
EFS        - File storage
Glacier    - Archive
```

### Database
```
RDS        - Relational DB
DynamoDB   - NoSQL
ElastiCache- In-memory
Redshift   - Data warehouse
```

### Identity
```
IAM        - Access management
Cognito    - User authentication
KMS        - Key management
```

## S3 Security

### Bucket Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::bucket/*"
  }]
}
```

### Access Control
```
Block public access
IAM policies
Bucket policies
Access Control Lists
Pre-signed URLs
```

### Common Mistakes
```
Public buckets
Misconfigured ACLs
Versioning not enabled
Logging disabled
```

## IAM

### Best Practices
```
Use IAM roles, not access keys
Principle of least privilege
MFA for privileged users
Regular audits
No root access keys
```

### Policy Structure
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject"],
    "Resource": "arn:aws:s3:::bucket/*"
  }]
}
```

## Azure

### Key Services
```
VM, App Service, Functions
Blob Storage, SQL Database
Azure AD, Key Vault
```

### Azure AD
```
MFA
Conditional Access
App registrations
Enterprise applications
```

## GCP

### Key Services
```
Compute Engine
Cloud Storage
BigQuery
Cloud Functions
IAM
```

### Key Management
```
Cloud KMS
Customer-managed keys
Cloud HSM
```

## Cloud Attacks

### Misconfiguration
```
S3 public buckets
Over permissive IAM
Open security groups
Unencrypted storage
```

### Privilege Escalation
```
Over-permissioned roles
Lambda with excessive roles
Service accounts
```

### Data Exfiltration
```
S3 download
Database export
Snapshot sharing
```

## Tools

### Enumeration
```bash
# AWS
aws configure
aws s3 ls
aws iam list-users

# Azure
az login
az vm list
az storage account list

# GCP
gcloud auth login
gcloud compute instances list
gsutil ls
```

### Scanning
```
Prowler       - AWS security
ScoutSuite    - Multi-cloud
CloudSploit   - AWS/Azure/GCP
```

## Defense

### Monitoring
```
CloudTrail (AWS)
Azure Monitor
Cloud Logging (GCP)
```

### Incident Response
```
Cloud-specific forensics
Log analysis
Evidence preservation
```

## Compliance

### Frameworks
```
CIS Benchmarks
SOC 2
ISO 27001
GDPR
HIPAA
```

## CTF Cloud Challenges
```
- Find exposed buckets
- IAM misconfiguration
- Metadata service exploitation
- SSRF to cloud credentials
```

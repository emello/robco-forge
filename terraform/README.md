# RobCo Forge Infrastructure

This directory contains Terraform configurations for deploying the RobCo Forge platform infrastructure on AWS.

## Structure

```
terraform/
├── modules/           # Reusable Terraform modules
│   ├── networking/    # VPC, subnets, NAT gateway, VPC endpoints
│   ├── eks/          # EKS cluster and node groups
│   ├── rds/          # RDS PostgreSQL database
│   ├── fsx/          # FSx for NetApp ONTAP filesystem
│   ├── workspaces/   # AWS WorkSpaces directory and configuration
│   └── monitoring/   # CloudWatch, Prometheus, Grafana
├── environments/     # Environment-specific configurations
│   ├── dev/         # Development environment
│   ├── staging/     # Staging environment
│   └── production/  # Production environment
└── backend.tf       # Remote state backend configuration
```

## Prerequisites

- Terraform >= 1.5.0
- AWS CLI configured with appropriate credentials
- S3 bucket for Terraform state (created separately)
- DynamoDB table for state locking (created separately)

## Usage

### Initialize Backend

First, create the S3 bucket and DynamoDB table for remote state:

```bash
# Create S3 bucket for state
aws s3api create-bucket \
  --bucket robco-forge-terraform-state \
  --region us-west-2 \
  --create-bucket-configuration LocationConstraint=us-west-2

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket robco-forge-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name robco-forge-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-west-2
```

### Deploy Environment

```bash
# Navigate to environment directory
cd environments/dev

# Initialize Terraform
terraform init

# Plan changes
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan
```

## Modules

### Networking Module
Creates isolated VPCs, private subnets across 3 AZs, NAT gateway with egress allowlist, and VPC endpoints.

### EKS Module
Deploys EKS cluster spanning 3 AZs with private API endpoint, node groups, and IRSA configuration.

### RDS Module
Creates RDS PostgreSQL 15 instance with Multi-AZ, encryption, automated backups, and read replica.

### FSx Module
Deploys FSx for NetApp ONTAP filesystem with encryption, backups, deduplication, and compression.

### WorkSpaces Module
Configures AWS WorkSpaces directory with Active Directory integration and WSP-only streaming.

### Monitoring Module
Sets up CloudWatch log groups, Prometheus, Grafana, alarms, and SNS topics.

## Security

- All resources use encryption at rest (AES-256)
- All traffic uses encryption in transit (TLS 1.3)
- Network isolation with no direct internet access for WorkSpaces
- Least-privilege IAM roles and security groups
- Audit logging enabled for all resources

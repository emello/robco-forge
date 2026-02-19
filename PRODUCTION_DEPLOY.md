# RobCo Forge - Production Deployment (Hackathon)

Quick deployment guide for production environment.

## Prerequisites

1. AWS credentials configured and valid
2. S3 bucket for Terraform state: `robco-forge-terraform-state`
3. DynamoDB table for state locking: `robco-forge-terraform-locks`

## Step 1: Update Configuration

Edit `terraform/environments/production/terraform.tfvars`:

```bash
# Update these values:
alert_email_addresses = ["your-email@example.com"]
directory_password = "YourStrongPassword123!"
active_directory_password = "YourStrongPassword123!"  # Same as above
```

## Step 2: Initialize Terraform

```bash
cd terraform/environments/production

# Initialize
terraform init

# Validate
terraform validate
```

## Step 3: Plan and Apply

```bash
# See what will be created
terraform plan

# Apply (will take 45-60 minutes)
terraform apply
```

## What Gets Created

### Network (5 min)
- VPC: 10.2.0.0/16
- 3 private subnets (WorkSpaces-compatible AZs)
- 1 public subnet (NAT Gateway)
- Security groups
- VPC endpoints (S3, Secrets Manager, FSx)

### EKS Cluster (15 min)
- Kubernetes 1.27
- 2 t3.large nodes
- Private API endpoint

### RDS PostgreSQL (10 min)
- db.t3.large instance
- 50GB storage (auto-scales to 200GB)
- Multi-AZ for HA

### AWS Managed Microsoft AD (40-45 min) ⏰
- Domain: robco.local
- Standard edition
- 2 domain controllers

### FSx ONTAP (15 min)
- 1TB storage
- 128 MB/s throughput
- Integrated with Active Directory

### Monitoring
- CloudWatch log groups
- SNS topic for alerts
- VPC Flow Logs

## Step 4: Capture Outputs

```bash
# Save all outputs
terraform output -json > outputs.json

# View specific outputs
terraform output eks_cluster_endpoint
terraform output rds_endpoint
terraform output workspaces_directory_id
terraform output fsx_filesystem_id
```

## Step 5: Configure kubectl

```bash
aws eks update-kubeconfig \
  --region us-east-1 \
  --name robco-forge-production

# Verify
kubectl get nodes
```

## Cost Estimate (Hackathon Duration)

Assuming 48 hours of runtime:

| Service | Cost/hour | 48h Total |
|---------|-----------|-----------|
| EKS Cluster | $0.10 | $4.80 |
| EC2 (3x t3.xlarge) | $0.50 | $24.00 |
| RDS (db.r6g.large) | $0.24 | $11.52 |
| AWS Managed AD | $0.12 | $5.76 |
| FSx ONTAP (1TB) | $0.23 | $11.04 |
| NAT Gateway | $0.05 | $2.40 |
| Data Transfer | ~$0.05 | ~$2.40 |
| **Total** | **~$1.29/hr** | **~$61.92** |

## Cleanup After Hackathon

```bash
cd terraform/environments/production

# Destroy everything
terraform destroy

# Confirm when prompted
```

## Troubleshooting

### AWS Credentials Expired
```bash
# Refresh your AWS session
# Then retry the command
```

### State Lock Error
```bash
# Force unlock (use Lock ID from error message)
terraform force-unlock <LOCK_ID>
```

### Subnet Conflicts
The networking module automatically selects WorkSpaces-compatible AZs. If you see subnet conflicts, run:
```bash
terraform destroy
terraform apply
```

## Next Steps After Infrastructure

1. Deploy Kubernetes resources (CDK)
2. Configure secrets in AWS Secrets Manager
3. Run database migrations
4. Deploy API to EKS
5. Deploy portal to Vercel
6. Configure domain (robcoforge.com)

See `DEPLOYMENT_PREPARATION.md` for detailed post-infrastructure steps.

## Quick Commands

```bash
# Check status
terraform show

# List resources
terraform state list

# View specific resource
terraform state show module.eks.aws_eks_cluster.main

# Refresh state
terraform refresh

# View plan without applying
terraform plan
```

## Support

- Terraform issues: Check CloudTrail logs
- AWS issues: Check AWS Console
- Network issues: Check VPC Flow Logs in CloudWatch

---

**Ready to deploy?**

```bash
cd terraform/environments/production
terraform init
terraform apply
```

Grab a coffee ☕ - this will take about 45-60 minutes!

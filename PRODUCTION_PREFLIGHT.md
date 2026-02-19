# Production Pre-Flight Checklist

Run these checks before deploying to production.

## 1. Verify All Fixes Are Present

```bash
# Check networking module has WorkSpaces AZ filtering
grep -A 5 "workspaces_az_ids_by_region" terraform/modules/networking/main.tf

# Check EKS module doesn't specify AMI version
grep -A 10 "aws_eks_node_group" terraform/modules/eks/main.tf | grep -i ami

# Check RDS has apply_method for static parameters
grep -A 2 "apply_method" terraform/modules/rds/main.tf

# Check FSx uses slice for 2 subnets
grep "slice.*0.*2" terraform/modules/fsx/main.tf

# Check WorkSpaces uses slice for 2 subnets
grep "slice.*0.*2" terraform/modules/workspaces/main.tf
```

Expected results:
- ✅ WorkSpaces AZ IDs defined for us-east-1
- ✅ No AMI version specified in EKS node group
- ✅ apply_method = "pending-reboot" found
- ✅ slice(var.private_subnet_ids, 0, 2) found in FSx
- ✅ slice(var.private_subnet_ids, 0, 2) found in WorkSpaces

## 2. Verify Production Configuration

```bash
cd terraform/environments/production

# Check Kubernetes version
grep kubernetes_version terraform.tfvars

# Check region
grep region terraform.tfvars

# Check VPC CIDR
grep vpc_cidr terraform.tfvars
```

Expected results:
- ✅ kubernetes_version = "1.27"
- ✅ region = "us-east-1"
- ✅ vpc_cidr = "10.2.0.0/16"

## 3. Update Secrets

Edit `terraform/environments/production/terraform.tfvars`:

```bash
# Required changes:
# 1. Update email
alert_email_addresses = ["your-email@example.com"]

# 2. Update passwords (must be same)
directory_password = "YourStrongPassword123!"
active_directory_password = "YourStrongPassword123!"
```

Password requirements:
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character

## 4. Verify AWS Credentials

```bash
# Check credentials are valid
aws sts get-caller-identity

# Check you're in the right region
aws configure get region

# Verify S3 backend exists
aws s3 ls s3://robco-forge-terraform-state/

# Verify DynamoDB table exists
aws dynamodb describe-table --table-name robco-forge-terraform-locks
```

Expected results:
- ✅ Valid AWS account ID returned
- ✅ Region is us-east-1
- ✅ S3 bucket exists
- ✅ DynamoDB table exists

## 5. Initialize Terraform

```bash
cd terraform/environments/production

# Initialize
terraform init

# Validate configuration
terraform validate

# Format check
terraform fmt -check
```

Expected results:
- ✅ Terraform initialized successfully
- ✅ Configuration is valid
- ✅ No formatting issues

## 6. Review Plan

```bash
# Generate plan
terraform plan -out=production.tfplan

# Review what will be created
terraform show production.tfplan
```

Expected resources to create: ~35

Key resources:
- ✅ VPC and subnets (4 subnets: 3 private, 1 public)
- ✅ EKS cluster and node group
- ✅ RDS PostgreSQL instance
- ✅ AWS Managed Microsoft AD
- ✅ FSx ONTAP filesystem
- ✅ Security groups
- ✅ VPC endpoints
- ✅ Monitoring resources

## 7. Cost Estimate

Review estimated costs:

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

## 8. Final Checks

- [ ] All fixes verified
- [ ] Configuration reviewed
- [ ] Secrets updated
- [ ] AWS credentials valid
- [ ] Terraform initialized
- [ ] Plan reviewed
- [ ] Cost estimate acceptable
- [ ] Ready to deploy

## 9. Deploy

```bash
# Apply the plan
terraform apply production.tfplan

# Or apply directly (will prompt for confirmation)
terraform apply
```

## 10. Monitor Deployment

Watch for these milestones:

- **5 min**: VPC, subnets, security groups created
- **15 min**: EKS cluster created
- **10 min**: RDS instance created
- **40-45 min**: AWS Managed Microsoft AD created ⏰ (longest wait)
- **15 min**: FSx ONTAP created (after AD completes)
- **60 min**: All resources created ✅

## Troubleshooting

### AWS Credentials Expired
```bash
# Refresh your AWS session
# Then retry: terraform apply
```

### State Lock Error
```bash
# Get lock ID from error message
terraform force-unlock <LOCK_ID>
```

### Subnet Conflict
```bash
# Destroy and recreate
terraform destroy
terraform apply
```

### Resource Already Exists
```bash
# Import existing resource
terraform import <resource_type>.<name> <resource_id>
```

---

## Ready to Deploy?

If all checks pass:

```bash
cd terraform/environments/production
terraform apply
```

☕ Grab a coffee - this will take 45-60 minutes!

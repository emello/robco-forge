# RobCo Forge Infrastructure Deployment Guide

This guide walks through deploying the RobCo Forge infrastructure using Terraform.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** >= 1.5.0 installed
3. **AWS CLI** configured with credentials
4. **Active Directory** credentials (for FSx and WorkSpaces integration)

## Initial Setup

### 1. Create Remote State Backend

Before deploying any environment, create the S3 bucket and DynamoDB table for Terraform state:

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

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket robco-forge-terraform-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name robco-forge-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-west-2
```

### 2. Configure Environment Variables

Create a `terraform.tfvars` file in your environment directory (copy from `terraform.tfvars.example`):

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and fill in the required values:

```hcl
# Active Directory passwords (use strong passwords!)
active_directory_password = "YOUR_STRONG_PASSWORD_HERE"
directory_password = "YOUR_STRONG_PASSWORD_HERE"

# Alert email addresses
alert_email_addresses = ["devops@robco.com", "platform-team@robco.com"]
```

**IMPORTANT**: Never commit `terraform.tfvars` to version control. It contains sensitive credentials.

## Deployment Steps

### Development Environment

```bash
cd terraform/environments/dev

# Initialize Terraform
terraform init

# Review the plan
terraform plan -out=tfplan

# Apply the changes
terraform apply tfplan
```

### Staging Environment

```bash
cd terraform/environments/staging

# Initialize Terraform
terraform init

# Review the plan
terraform plan -out=tfplan

# Apply the changes (requires approval)
terraform apply tfplan
```

### Production Environment

```bash
cd terraform/environments/production

# Initialize Terraform
terraform init

# Review the plan
terraform plan -out=tfplan

# Apply the changes (requires approval and review)
terraform apply tfplan
```

## Post-Deployment Configuration

### 1. Configure kubectl for EKS

```bash
# Get EKS cluster credentials
aws eks update-kubeconfig \
  --region us-west-2 \
  --name dev-forge-cluster

# Verify connection
kubectl get nodes
```

### 2. Configure Active Directory Integration

After the WorkSpaces directory is created, you'll need to:

1. Note the Directory DNS IP addresses from Terraform outputs
2. Update the FSx module's `active_directory_dns_ips` variable
3. Re-run `terraform apply` to update FSx with the correct DNS IPs

```bash
# Get directory DNS IPs
terraform output directory_dns_ips

# Update terraform.tfvars
active_directory_dns_ips = ["10.0.1.10", "10.0.2.10"]

# Re-apply
terraform apply
```

### 3. Configure Group Policies for WorkSpaces

To enforce WSP-only and data exfiltration prevention:

1. Connect to the WorkSpaces directory domain controller
2. Apply the following Group Policies:
   - Disable PCoIP protocol
   - Disable clipboard operations
   - Disable USB device redirection
   - Disable drive redirection
   - Disable file transfer
   - Disable printing
   - Enable screen watermarking

See `docs/group-policies.md` for detailed instructions (to be created).

### 4. Verify Monitoring

```bash
# Check CloudWatch dashboard
aws cloudwatch get-dashboard \
  --dashboard-name dev-forge-dashboard \
  --region us-west-2

# Verify SNS topic
aws sns list-subscriptions-by-topic \
  --topic-arn $(terraform output -raw sns_topic_arn) \
  --region us-west-2
```

## Outputs

After deployment, Terraform provides the following outputs:

- **VPC ID**: For network configuration
- **EKS Cluster Name**: For kubectl configuration
- **RDS Endpoint**: For database connections
- **FSx DNS Name**: For user volume mounting
- **WorkSpaces Directory ID**: For WorkSpace provisioning
- **SNS Topic ARN**: For alert subscriptions

View all outputs:

```bash
terraform output
```

## Troubleshooting

### FSx Fails to Join Active Directory

**Issue**: FSx ONTAP fails to join the Active Directory domain.

**Solution**:
1. Verify the Active Directory DNS IPs are correct
2. Ensure the service account has permissions to join computers to the domain
3. Check the OU distinguished name is correct
4. Verify network connectivity between FSx and the directory

### WorkSpaces Directory Creation Fails

**Issue**: WorkSpaces directory creation fails or times out.

**Solution**:
1. Ensure you have at least 2 private subnets in different AZs
2. Verify the directory password meets complexity requirements
3. Check AWS service limits for Directory Service

### EKS Nodes Not Joining Cluster

**Issue**: EKS nodes are created but don't join the cluster.

**Solution**:
1. Verify the node IAM role has the correct policies attached
2. Check security group rules allow communication between nodes and control plane
3. Review CloudWatch logs for the EKS cluster

## Cleanup

To destroy the infrastructure:

```bash
cd terraform/environments/dev

# Plan the destruction
terraform plan -destroy -out=destroy.tfplan

# Review carefully, then destroy
terraform apply destroy.tfplan
```

**WARNING**: This will delete all resources including databases and file systems. Ensure you have backups before proceeding.

## Security Considerations

1. **Secrets Management**: All passwords are stored in AWS Secrets Manager
2. **Encryption**: All data is encrypted at rest (AES-256) and in transit (TLS 1.3)
3. **Network Isolation**: WorkSpaces have no direct internet access
4. **Least Privilege**: All IAM roles follow least-privilege principles
5. **Audit Logging**: VPC Flow Logs and CloudWatch logs capture all activity

## Cost Optimization

Estimated monthly costs by environment:

- **Development**: ~$500-800/month
  - EKS: ~$150
  - RDS: ~$100
  - FSx: ~$200
  - WorkSpaces Directory: ~$50
  - Data Transfer: ~$50

- **Staging**: ~$1,000-1,500/month
- **Production**: ~$3,000-5,000/month (varies with WorkSpace usage)

To reduce costs:
1. Stop unused WorkSpaces
2. Use smaller instance types for dev/staging
3. Enable FSx deduplication and compression
4. Use RDS reserved instances for production

## Next Steps

After infrastructure deployment:

1. Deploy Kubernetes applications using AWS CDK (Task 2)
2. Deploy Forge API services (Phase 2)
3. Configure Lucy AI service (Phase 5)
4. Set up CI/CD pipelines (Phase 15)

## Support

For issues or questions:
- Check CloudWatch logs: `/aws/forge/{environment}/`
- Review Terraform state: `terraform show`
- Contact platform team: platform-team@robco.com

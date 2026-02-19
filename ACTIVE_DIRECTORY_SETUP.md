# Active Directory Setup for RobCo Forge

## Problem

The RobCo Forge platform requires Active Directory for:
1. **FSx ONTAP** - User volume storage with AD integration
2. **WorkSpaces** - Directory services for user authentication

## Solutions

You have **three options** for setting up Active Directory:

---

## Option 1: AWS Managed Microsoft AD (Recommended for Production)

### Pros:
- Fully managed by AWS
- High availability (Multi-AZ)
- Automatic backups and patching
- Integrated with AWS services

### Cons:
- Additional cost (~$100-200/month)
- Takes 20-40 minutes to provision

### Steps:

1. **Create AWS Managed Microsoft AD:**
   ```bash
   aws ds create-microsoft-ad \
     --name staging.robco.local \
     --password "YourStrongPassword123!" \
     --edition Standard \
     --vpc-settings VpcId=vpc-xxxxx,SubnetIds=subnet-xxxxx,subnet-yyyyy
   ```

2. **Wait for directory to be Active:**
   ```bash
   aws ds describe-directories --directory-ids d-xxxxx
   ```

3. **Get DNS IP addresses:**
   ```bash
   aws ds describe-directories \
     --directory-ids d-xxxxx \
     --query 'DirectoryDescriptions[0].DnsIpAddrs' \
     --output json
   ```

4. **Update terraform.tfvars:**
   ```hcl
   active_directory_domain_name = "staging.robco.local"
   active_directory_dns_ips = ["10.1.0.10", "10.1.0.11"]  # From step 3
   active_directory_username = "Admin"
   active_directory_password = "YourStrongPassword123!"
   ```

---

## Option 2: AWS Simple AD (Good for Testing/Dev)

### Pros:
- Lower cost (~$40/month)
- Faster to set up
- Good for development/testing

### Cons:
- Not a full Microsoft AD (Samba-based)
- Limited features
- Not recommended for production

### Steps:

1. **Create Simple AD:**
   ```bash
   aws ds create-directory \
     --name staging.robco.local \
     --password "YourStrongPassword123!" \
     --size Small \
     --vpc-settings VpcId=vpc-xxxxx,SubnetIds=subnet-xxxxx,subnet-yyyyy
   ```

2. **Get DNS IP addresses:**
   ```bash
   aws ds describe-directories \
     --directory-ids d-xxxxx \
     --query 'DirectoryDescriptions[0].DnsIpAddrs'
   ```

3. **Update terraform.tfvars:**
   ```hcl
   directory_type = "SimpleAD"
   active_directory_domain_name = "staging.robco.local"
   active_directory_dns_ips = ["10.1.0.10", "10.1.0.11"]
   active_directory_username = "Administrator"
   active_directory_password = "YourStrongPassword123!"
   ```

---

## Option 3: Skip AD for Now (Minimal Deployment)

If you want to test the infrastructure without AD, you can temporarily disable FSx and WorkSpaces modules.

### Steps:

1. **Comment out FSx module in staging/main.tf:**
   ```hcl
   # module "fsx" {
   #   source = "../../modules/fsx"
   #   ...
   # }
   ```

2. **Comment out WorkSpaces module:**
   ```hcl
   # module "workspaces" {
   #   source = "../../modules/workspaces"
   #   ...
   # }
   ```

3. **Deploy core infrastructure:**
   ```bash
   terraform apply
   ```

4. **Later, uncomment and add AD configuration**

**⚠️ Warning:** This gives you a partial deployment without the core WorkSpaces functionality.

---

## Quick Start: Use AWS Managed Microsoft AD

For the fastest path to a working deployment:

### 1. Create the directory first (outside Terraform):

```bash
# Get your VPC ID
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=*forge*" --query 'Vpcs[0].VpcId' --output text)

# Get private subnet IDs
SUBNET_IDS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=*private*" \
  --query 'Subnets[0:2].SubnetId' \
  --output text | tr '\t' ',')

# Create Managed AD
aws ds create-microsoft-ad \
  --name staging.robco.local \
  --password "ChangeMe123!StrongPassword" \
  --edition Standard \
  --vpc-settings "VpcId=$VPC_ID,SubnetIds=$SUBNET_IDS"
```

### 2. Wait for it to be Active (20-40 minutes):

```bash
# Check status
aws ds describe-directories --query 'DirectoryDescriptions[*].[DirectoryId,Name,Stage]' --output table

# Wait until Stage shows "Active"
```

### 3. Get DNS IPs:

```bash
DIRECTORY_ID=$(aws ds describe-directories --query 'DirectoryDescriptions[0].DirectoryId' --output text)

aws ds describe-directories \
  --directory-ids $DIRECTORY_ID \
  --query 'DirectoryDescriptions[0].DnsIpAddrs' \
  --output json
```

### 4. Update terraform.tfvars:

```hcl
active_directory_domain_name = "staging.robco.local"
active_directory_dns_ips = ["10.1.0.10", "10.1.0.11"]  # From step 3
active_directory_username = "Admin"
active_directory_password = "ChangeMe123!StrongPassword"  # Same as step 1
```

### 5. Run Terraform:

```bash
terraform plan
terraform apply
```

---

## Current Error Fix

For your immediate error, you need to either:

1. **Set up AD first** (Option 1 or 2 above), then update `terraform.tfvars`
2. **Use placeholder values** in `terraform.tfvars` (will fail at apply, but passes validation)
3. **Comment out FSx/WorkSpaces modules** (Option 3 above)

---

## Recommended Path

For a production-ready deployment:

1. ✅ Create AWS Managed Microsoft AD (20-40 min wait)
2. ✅ Update terraform.tfvars with real DNS IPs
3. ✅ Run terraform apply
4. ✅ Complete deployment

For quick testing:
1. ✅ Use Simple AD (faster, cheaper)
2. ✅ Or comment out FSx/WorkSpaces modules temporarily

---

## Password Requirements

Active Directory passwords must:
- Be at least 8 characters
- Contain uppercase and lowercase letters
- Contain numbers
- Contain special characters
- Not contain the username

Example strong password: `Forge2026!Secure#Pass`

---

## Cost Estimates

- **AWS Managed Microsoft AD (Standard)**: ~$100/month
- **AWS Managed Microsoft AD (Enterprise)**: ~$200/month
- **Simple AD (Small)**: ~$40/month
- **Simple AD (Large)**: ~$80/month

---

## Next Steps

1. Choose your AD option
2. Set it up
3. Update `terraform/environments/staging/terraform.tfvars`
4. Run `terraform plan` and `terraform apply`

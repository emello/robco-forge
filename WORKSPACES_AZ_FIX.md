# WorkSpaces Availability Zone Compatibility Fix

## Important Note
This requirement **only applies to WorkSpaces Personal**. It does NOT apply to:
- WorkSpaces Applications
- AWS Managed Microsoft AD (MAD)
- Simple AD

Since RobCo Forge uses **WorkSpaces Personal**, this fix ensures compatibility.

## Issue
WorkSpaces Personal only works in specific Availability Zones (AZ IDs) per region. The networking module has been updated to automatically filter for WorkSpaces-compatible AZs.

## What Changed

### Before
```hcl
locals {
  azs = slice(data.aws_availability_zones.available.names, 0, 3)
}
```

### After
```hcl
locals {
  # WorkSpaces-compatible AZ IDs by region
  workspaces_az_ids_by_region = {
    "us-east-1" = ["use1-az2", "use1-az4", "use1-az6"]
    # ... other regions
  }
  
  # Filter AZs to only include WorkSpaces-compatible ones
  workspaces_compatible_azs = [
    for az in data.aws_availability_zones.available.names :
    az if contains(local.workspaces_az_ids, ...)
  ]
  
  azs = slice(local.workspaces_compatible_azs, 0, min(3, length(local.workspaces_compatible_azs)))
}
```

## For us-east-1 (Your Current Region)

WorkSpaces-compatible AZ IDs:
- `use1-az2`
- `use1-az4`
- `use1-az6`

These map to specific Availability Zones in your account (e.g., us-east-1a, us-east-1b, etc.)

## Impact on Current Deployment

### If Terraform is Still Running
The fix will be applied automatically. Terraform will:
1. Detect that subnets need to be recreated in different AZs
2. Show a plan to destroy and recreate subnets
3. This will cascade to resources that depend on subnets

**⚠️ WARNING**: This will require recreating:
- Subnets
- NAT Gateway
- Potentially EKS, RDS, FSx, WorkSpaces (if already created)

### If Terraform Already Completed
You have two options:

#### Option 1: Accept Current AZs (If They're Compatible)
Check if your current subnets are already in WorkSpaces-compatible AZs:

```bash
# Get current subnet AZ IDs
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=YOUR_VPC_ID" \
  --query 'Subnets[*].[SubnetId,AvailabilityZone,AvailabilityZoneId]' \
  --output table

# Check if AZ IDs are in: use1-az2, use1-az4, use1-az6
```

If your subnets are already in compatible AZs, you're good! No changes needed.

#### Option 2: Recreate Infrastructure (If Not Compatible)
If your subnets are NOT in WorkSpaces-compatible AZs:

```bash
cd terraform/environments/staging

# Destroy current infrastructure
terraform destroy

# Re-apply with the fix
terraform apply
```

**⚠️ WARNING**: This will destroy all resources and start over.

## Verification

After deployment, verify subnets are in WorkSpaces-compatible AZs:

```bash
# Get subnet AZ IDs
aws ec2 describe-subnets \
  --filters "Name=tag:Name,Values=staging-private-subnet-*" \
  --query 'Subnets[*].[Tags[?Key==`Name`].Value|[0],AvailabilityZone,AvailabilityZoneId]' \
  --output table

# Expected AZ IDs for us-east-1: use1-az2, use1-az4, use1-az6
```

## Supported Regions

The fix includes all WorkSpaces-supported regions:
- US East (N. Virginia) - us-east-1
- US West (Oregon) - us-west-2
- Asia Pacific (Mumbai) - ap-south-1
- Asia Pacific (Seoul) - ap-northeast-2
- Asia Pacific (Singapore) - ap-southeast-1
- Asia Pacific (Sydney) - ap-southeast-2
- Asia Pacific (Tokyo) - ap-northeast-1
- Canada (Central) - ca-central-1
- Europe (Frankfurt) - eu-central-1
- Europe (Ireland) - eu-west-1
- Europe (London) - eu-west-2
- Europe (Paris) - eu-west-3
- South America (São Paulo) - sa-east-1
- Africa (Cape Town) - af-south-1
- Israel (Tel Aviv) - il-central-1
- AWS GovCloud (US-West) - us-gov-west-1
- AWS GovCloud (US-East) - us-gov-east-1

## Reference
- [AWS WorkSpaces Availability Zones Documentation](https://docs.aws.amazon.com/workspaces/latest/adminguide/azs-workspaces.html)


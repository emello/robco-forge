# RobCo Forge - Troubleshooting Guide

## Common Deployment Issues

### Issue 1: S3 Bucket Does Not Exist (Terraform Backend)

**Error Message:**
```
Failed to get existing workspaces: S3 bucket does not exist.
The referenced S3 bucket must have been previously created.
```

**Cause:** Terraform is configured to use an S3 bucket for remote state storage, but the bucket hasn't been created yet.

**Solution:**

#### Option A: Run the Setup Script (Recommended)

**On Windows (PowerShell):**
```powershell
.\setup-terraform-backend.ps1
# Or specify a different region:
.\setup-terraform-backend.ps1 -AwsRegion us-west-2
```

**On Linux/Mac (Bash):**
```bash
chmod +x setup-terraform-backend.sh
./setup-terraform-backend.sh
# Or specify a different region:
./setup-terraform-backend.sh us-west-2
```

#### Option B: Manual Setup

1. **Create the S3 bucket:**
   ```bash
   # For us-east-1
   aws s3api create-bucket \
     --bucket robco-forge-terraform-state \
     --region us-east-1

   # For other regions (replace us-west-2 with your region)
   aws s3api create-bucket \
     --bucket robco-forge-terraform-state \
     --region us-west-2 \
     --create-bucket-configuration LocationConstraint=us-west-2
   ```

2. **Enable versioning:**
   ```bash
   aws s3api put-bucket-versioning \
     --bucket robco-forge-terraform-state \
     --versioning-configuration Status=Enabled
   ```

3. **Enable encryption:**
   ```bash
   aws s3api put-bucket-encryption \
     --bucket robco-forge-terraform-state \
     --server-side-encryption-configuration '{
       "Rules": [{
         "ApplyServerSideEncryptionByDefault": {
           "SSEAlgorithm": "AES256"
         }
       }]
     }'
   ```

4. **Block public access:**
   ```bash
   aws s3api put-public-access-block \
     --bucket robco-forge-terraform-state \
     --public-access-block-configuration \
       "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
   ```

5. **Create DynamoDB table for state locking:**
   ```bash
   aws dynamodb create-table \
     --table-name robco-forge-terraform-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
     --region us-east-1
   ```

6. **Wait for table to be ready:**
   ```bash
   aws dynamodb wait table-exists \
     --table-name robco-forge-terraform-locks \
     --region us-east-1
   ```

#### Option C: Use Local State (Not Recommended for Production)

If you want to skip remote state for testing:

1. Comment out the backend configuration in your Terraform files:
   ```hcl
   # terraform {
   #   backend "s3" {
   #     bucket = "robco-forge-terraform-state"
   #     ...
   #   }
   # }
   ```

2. Run `terraform init` again

**⚠️ Warning:** Local state is not recommended for production or team environments.

---

### Issue 2: AWS CLI Not Configured

**Error Message:**
```
Unable to locate credentials
```

**Solution:**
```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-east-1)
- Default output format (json)

---

### Issue 3: Insufficient AWS Permissions

**Error Message:**
```
AccessDenied: User is not authorized to perform...
```

**Solution:**

Ensure your AWS user/role has the following permissions:
- S3: Full access to create and manage buckets
- DynamoDB: Full access to create and manage tables
- EC2: Full access for VPC, subnets, security groups
- EKS: Full access for cluster management
- RDS: Full access for database management
- FSx: Full access for filesystem management
- WorkSpaces: Full access for directory and workspace management
- IAM: Permissions to create roles and policies
- CloudWatch: Permissions to create log groups and alarms
- Secrets Manager: Full access

For testing, you can use the `AdministratorAccess` policy, but for production, create a custom policy with least-privilege access.

---

### Issue 4: Terraform Init Fails

**Error Message:**
```
Error: Failed to install provider
```

**Solution:**

1. Check internet connectivity
2. Clear Terraform cache:
   ```bash
   rm -rf .terraform
   rm .terraform.lock.hcl
   ```
3. Run `terraform init` again

---

### Issue 5: Region Mismatch

**Error Message:**
```
Error: The bucket you are attempting to access must be addressed using the specified endpoint
```

**Solution:**

Ensure the region in your Terraform backend configuration matches the region where you created the S3 bucket.

Update `terraform/environments/staging/main.tf`:
```hcl
terraform {
  backend "s3" {
    bucket         = "robco-forge-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "us-east-1"  # Match this with your bucket region
    dynamodb_table = "robco-forge-terraform-locks"
    encrypt        = true
  }
}
```

---

### Issue 6: Bucket Name Already Taken

**Error Message:**
```
BucketAlreadyExists: The requested bucket name is not available
```

**Solution:**

S3 bucket names must be globally unique. Update the bucket name in all Terraform files:

1. Choose a unique name: `robco-forge-terraform-state-YOUR-ORG-NAME`
2. Update in:
   - `terraform/backend.tf`
   - `terraform/environments/dev/main.tf`
   - `terraform/environments/staging/main.tf`
   - `terraform/environments/production/main.tf`
3. Create the bucket with the new name
4. Run `terraform init` again

---

### Issue 7: DynamoDB Table Already Exists

**Error Message:**
```
ResourceInUseException: Table already exists
```

**Solution:**

This is usually fine - the table already exists from a previous setup. You can:

1. Use the existing table (recommended)
2. Or delete and recreate:
   ```bash
   aws dynamodb delete-table \
     --table-name robco-forge-terraform-locks \
     --region us-east-1
   
   # Wait a moment, then recreate
   aws dynamodb create-table \
     --table-name robco-forge-terraform-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
     --region us-east-1
   ```

---

## Verification Steps

After setting up the backend, verify everything is working:

### 1. Check S3 Bucket
```bash
aws s3 ls robco-forge-terraform-state
```

### 2. Check DynamoDB Table
```bash
aws dynamodb describe-table \
  --table-name robco-forge-terraform-locks \
  --region us-east-1
```

### 3. Test Terraform Init
```bash
cd terraform/environments/staging
terraform init
```

You should see:
```
Initializing the backend...
Successfully configured the backend "s3"!
```

---

## Quick Fixes

### Reset Terraform State
```bash
cd terraform/environments/staging
rm -rf .terraform
rm .terraform.lock.hcl
terraform init
```

### Check AWS Configuration
```bash
aws sts get-caller-identity
aws configure list
```

### Verify AWS Region
```bash
aws configure get region
```

### List All S3 Buckets
```bash
aws s3 ls
```

### List All DynamoDB Tables
```bash
aws dynamodb list-tables --region us-east-1
```

---

## Getting Help

If you're still experiencing issues:

1. **Check AWS CloudTrail** for detailed error messages
2. **Review Terraform logs** with `TF_LOG=DEBUG terraform init`
3. **Verify IAM permissions** in AWS Console
4. **Check AWS Service Health Dashboard** for outages
5. **Review the DEPLOYMENT_GUIDE.md** for detailed instructions

---

## Next Steps

Once the backend is set up successfully:

1. Continue with infrastructure deployment:
   ```bash
   cd terraform/environments/staging
   terraform plan
   terraform apply
   ```

2. Follow the rest of the deployment guide in **DEPLOYMENT_CHECKLIST.md**

---

**Need more help?** Check the other documentation files:
- **QUICK_DEPLOY.md** - Quick reference
- **DEPLOYMENT_CHECKLIST.md** - Complete checklist
- **DEPLOYMENT_GUIDE.md** - Detailed guide

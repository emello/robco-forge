# RobCo Forge - Terraform Backend Setup Script (PowerShell)
# This script creates the S3 bucket and DynamoDB table for Terraform state management

param(
    [string]$AwsRegion = "us-east-1"
)

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Terraform Backend Setup" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

Write-Host "Using AWS Region: $AwsRegion" -ForegroundColor Blue
Write-Host ""

# Configuration
$BucketName = "robco-forge-terraform-state"
$DynamoDBTable = "robco-forge-terraform-locks"

# Check if AWS CLI is configured
Write-Host "Checking AWS CLI configuration..." -ForegroundColor Blue
try {
    $null = aws sts get-caller-identity 2>&1
    Write-Host "✓ AWS CLI is configured" -ForegroundColor Green
} catch {
    Write-Host "✗ AWS CLI is not configured. Please run 'aws configure' first." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Get AWS account ID
$AwsAccountId = aws sts get-caller-identity --query Account --output text
Write-Host "AWS Account ID: $AwsAccountId" -ForegroundColor Blue
Write-Host ""

# Create S3 bucket for Terraform state
Write-Host "Creating S3 bucket: $BucketName" -ForegroundColor Blue

$bucketExists = $false
try {
    $null = aws s3 ls "s3://$BucketName" 2>&1
    $bucketExists = $true
} catch {
    $bucketExists = $false
}

if (-not $bucketExists) {
    # Bucket doesn't exist, create it
    if ($AwsRegion -eq "us-east-1") {
        # us-east-1 doesn't need LocationConstraint
        aws s3api create-bucket --bucket $BucketName --region $AwsRegion
    } else {
        # Other regions need LocationConstraint
        aws s3api create-bucket --bucket $BucketName --region $AwsRegion --create-bucket-configuration LocationConstraint=$AwsRegion
    }
    Write-Host "✓ S3 bucket created: $BucketName" -ForegroundColor Green
} else {
    Write-Host "⚠ S3 bucket already exists: $BucketName" -ForegroundColor Yellow
}

# Enable versioning on the bucket
Write-Host "Enabling versioning on S3 bucket..." -ForegroundColor Blue
aws s3api put-bucket-versioning --bucket $BucketName --versioning-configuration Status=Enabled
Write-Host "✓ Versioning enabled" -ForegroundColor Green

# Enable encryption on the bucket
Write-Host "Enabling encryption on S3 bucket..." -ForegroundColor Blue
$encryptionConfig = @'
{
    "Rules": [{
        "ApplyServerSideEncryptionByDefault": {
            "SSEAlgorithm": "AES256"
        }
    }]
}
'@
aws s3api put-bucket-encryption --bucket $BucketName --server-side-encryption-configuration $encryptionConfig
Write-Host "✓ Encryption enabled" -ForegroundColor Green

# Block public access
Write-Host "Blocking public access on S3 bucket..." -ForegroundColor Blue
aws s3api put-public-access-block --bucket $BucketName --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
Write-Host "✓ Public access blocked" -ForegroundColor Green
Write-Host ""

# Create DynamoDB table for state locking
Write-Host "Creating DynamoDB table: $DynamoDBTable" -ForegroundColor Blue

$tableExists = $false
try {
    $null = aws dynamodb describe-table --table-name $DynamoDBTable --region $AwsRegion 2>&1
    $tableExists = $true
} catch {
    $tableExists = $false
}

if ($tableExists) {
    Write-Host "⚠ DynamoDB table already exists: $DynamoDBTable" -ForegroundColor Yellow
} else {
    aws dynamodb create-table `
        --table-name $DynamoDBTable `
        --attribute-definitions AttributeName=LockID,AttributeType=S `
        --key-schema AttributeName=LockID,KeyType=HASH `
        --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 `
        --region $AwsRegion
    
    Write-Host "Waiting for DynamoDB table to be active..." -ForegroundColor Blue
    aws dynamodb wait table-exists --table-name $DynamoDBTable --region $AwsRegion
    Write-Host "✓ DynamoDB table created: $DynamoDBTable" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Terraform Backend Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Resources created:" -ForegroundColor Blue
Write-Host "✓ S3 Bucket: $BucketName" -ForegroundColor Green
Write-Host "✓ DynamoDB Table: $DynamoDBTable" -ForegroundColor Green
Write-Host "✓ Region: $AwsRegion" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run Terraform commands:" -ForegroundColor Blue
Write-Host "  cd terraform/environments/staging" -ForegroundColor Cyan
Write-Host "  terraform init" -ForegroundColor Cyan
Write-Host "  terraform plan" -ForegroundColor Cyan
Write-Host ""

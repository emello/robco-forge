#!/bin/bash

# RobCo Forge - Terraform Backend Setup Script
# This script creates the S3 bucket and DynamoDB table for Terraform state management

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Terraform Backend Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get AWS region
AWS_REGION=${1:-us-east-1}
echo -e "${BLUE}Using AWS Region: ${AWS_REGION}${NC}"
echo ""

# Configuration
BUCKET_NAME="robco-forge-terraform-state"
DYNAMODB_TABLE="robco-forge-terraform-locks"

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if AWS CLI is configured
print_info "Checking AWS CLI configuration..."
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi
print_status "AWS CLI is configured"
echo ""

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_info "AWS Account ID: ${AWS_ACCOUNT_ID}"
echo ""

# Create S3 bucket for Terraform state
print_info "Creating S3 bucket: ${BUCKET_NAME}"

if aws s3 ls "s3://${BUCKET_NAME}" 2>&1 | grep -q 'NoSuchBucket'; then
    # Bucket doesn't exist, create it
    if [ "$AWS_REGION" = "us-east-1" ]; then
        # us-east-1 doesn't need LocationConstraint
        aws s3api create-bucket \
            --bucket ${BUCKET_NAME} \
            --region ${AWS_REGION}
    else
        # Other regions need LocationConstraint
        aws s3api create-bucket \
            --bucket ${BUCKET_NAME} \
            --region ${AWS_REGION} \
            --create-bucket-configuration LocationConstraint=${AWS_REGION}
    fi
    print_status "S3 bucket created: ${BUCKET_NAME}"
else
    print_warning "S3 bucket already exists: ${BUCKET_NAME}"
fi

# Enable versioning on the bucket
print_info "Enabling versioning on S3 bucket..."
aws s3api put-bucket-versioning \
    --bucket ${BUCKET_NAME} \
    --versioning-configuration Status=Enabled
print_status "Versioning enabled"

# Enable encryption on the bucket
print_info "Enabling encryption on S3 bucket..."
aws s3api put-bucket-encryption \
    --bucket ${BUCKET_NAME} \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'
print_status "Encryption enabled"

# Block public access
print_info "Blocking public access on S3 bucket..."
aws s3api put-public-access-block \
    --bucket ${BUCKET_NAME} \
    --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
print_status "Public access blocked"

echo ""

# Create DynamoDB table for state locking
print_info "Creating DynamoDB table: ${DYNAMODB_TABLE}"

if aws dynamodb describe-table --table-name ${DYNAMODB_TABLE} --region ${AWS_REGION} &> /dev/null; then
    print_warning "DynamoDB table already exists: ${DYNAMODB_TABLE}"
else
    aws dynamodb create-table \
        --table-name ${DYNAMODB_TABLE} \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
        --region ${AWS_REGION}
    
    print_info "Waiting for DynamoDB table to be active..."
    aws dynamodb wait table-exists --table-name ${DYNAMODB_TABLE} --region ${AWS_REGION}
    print_status "DynamoDB table created: ${DYNAMODB_TABLE}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Terraform Backend Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
print_info "Resources created:"
print_status "S3 Bucket: ${BUCKET_NAME}"
print_status "DynamoDB Table: ${DYNAMODB_TABLE}"
print_status "Region: ${AWS_REGION}"
echo ""
print_info "You can now run Terraform commands:"
echo -e "  ${BLUE}cd terraform/environments/staging${NC}"
echo -e "  ${BLUE}terraform init${NC}"
echo -e "  ${BLUE}terraform plan${NC}"
echo ""

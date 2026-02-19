#!/bin/bash

# Check if current subnets are in WorkSpaces-compatible AZs
# For us-east-1, compatible AZ IDs are: use1-az2, use1-az4, use1-az6

echo "Checking WorkSpaces AZ compatibility..."
echo ""

# Get VPC ID
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=staging-workspaces-vpc" \
  --query 'Vpcs[0].VpcId' \
  --output text 2>/dev/null)

if [ "$VPC_ID" == "None" ] || [ -z "$VPC_ID" ]; then
  echo "✅ VPC not yet created - will use WorkSpaces-compatible AZs"
  exit 0
fi

echo "VPC ID: $VPC_ID"
echo ""

# Get private subnets
echo "Private Subnets:"
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Tier,Values=private" \
  --query 'Subnets[*].[Tags[?Key==`Name`].Value|[0],AvailabilityZone,AvailabilityZoneId]' \
  --output table

echo ""

# Get AZ IDs
AZ_IDS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Tier,Values=private" \
  --query 'Subnets[*].AvailabilityZoneId' \
  --output text)

echo "Current AZ IDs: $AZ_IDS"
echo ""

# Check compatibility for us-east-1
COMPATIBLE_AZS="use1-az2 use1-az4 use1-az6"
ALL_COMPATIBLE=true

for AZ_ID in $AZ_IDS; do
  if echo "$COMPATIBLE_AZS" | grep -q "$AZ_ID"; then
    echo "✅ $AZ_ID is WorkSpaces-compatible"
  else
    echo "❌ $AZ_ID is NOT WorkSpaces-compatible"
    ALL_COMPATIBLE=false
  fi
done

echo ""

if [ "$ALL_COMPATIBLE" = true ]; then
  echo "✅ All subnets are in WorkSpaces-compatible AZs"
  echo "   No changes needed!"
else
  echo "⚠️  Some subnets are NOT in WorkSpaces-compatible AZs"
  echo "   You may need to recreate the infrastructure"
  echo ""
  echo "   Options:"
  echo "   1. Let Terraform recreate subnets (will destroy/recreate resources)"
  echo "   2. Destroy and re-apply infrastructure"
fi


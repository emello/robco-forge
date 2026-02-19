#!/bin/bash

# RobCo Forge - Fix Terraform Region Mismatch
# This script reinitializes Terraform after region configuration changes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Fixing Terraform Region Configuration${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get environment
ENVIRONMENT=${1:-staging}
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo ""

# Navigate to environment directory
cd "terraform/environments/${ENVIRONMENT}"

echo -e "${YELLOW}⚠${NC} Removing old Terraform state..."
rm -rf .terraform
rm -f .terraform.lock.hcl

echo -e "${GREEN}✓${NC} Old state removed"
echo ""

echo -e "${BLUE}ℹ${NC} Reinitializing Terraform with correct region (us-east-1)..."
terraform init

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Terraform Region Fix Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}ℹ${NC} You can now run:"
echo -e "  ${BLUE}terraform plan${NC}"
echo -e "  ${BLUE}terraform apply${NC}"
echo ""

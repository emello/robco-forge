# RobCo Forge - Infrastructure Validation Guide

## Overview

This guide helps you validate the Phase 1 infrastructure deployment for RobCo Forge. The validation ensures all Terraform modules, EKS cluster, databases, file systems, and Kubernetes resources are properly deployed and accessible.

## What Gets Validated

### Automated Checks
1. ✅ Terraform deployment and state
2. ✅ EKS cluster health and node status
3. ✅ RDS PostgreSQL accessibility from EKS
4. ✅ FSx ONTAP accessibility from EKS
5. ✅ WorkSpaces directory configuration
6. ✅ Kubernetes namespaces and service accounts
7. ✅ IRSA (IAM Roles for Service Accounts) configuration
8. ✅ Monitoring infrastructure (CloudWatch, SNS)

### Manual Verification Required
- WSP-only configuration (PCoIP disabled)
- Group Policies for data exfiltration prevention
- Active Directory integration

## Quick Start

### Option 1: Automated Validation Script (Recommended)

```bash
# Navigate to project root
cd /path/to/robco-forge

# Make script executable (Linux/Mac)
chmod +x scripts/validate-infrastructure.sh

# Run validation for dev environment
./scripts/validate-infrastructure.sh dev us-west-2

# For other environments
./scripts/validate-infrastructure.sh staging us-west-2
./scripts/validate-infrastructure.sh production us-west-2
```

**Expected Result:** Script exits with code 0 and shows all green checkmarks (✓)

### Option 2: Manual Validation

Follow the comprehensive checklist:

```bash
# View the checklist
cat docs/infrastructure-validation-checklist.md
```

## Prerequisites

Before running validation:

1. **AWS CLI** configured with appropriate credentials
   ```bash
   aws sts get-caller-identity
   ```

2. **kubectl** installed and configured
   ```bash
   kubectl version --client
   ```

3. **Terraform** installed
   ```bash
   terraform version
   ```

4. **Access to EKS cluster**
   ```bash
   aws eks update-kubeconfig --name robco-forge-dev --region us-west-2
   kubectl get nodes
   ```

## Validation Steps

### Step 1: Verify Terraform Deployment

```bash
cd terraform/environments/dev
terraform state list
terraform output
```

**Expected Outputs:**
- vpc_id
- eks_cluster_name
- rds_endpoint
- fsx_dns_name
- workspaces_directory_id
- sns_topic_arn

### Step 2: Verify EKS Cluster

```bash
# Check cluster status
aws eks describe-cluster --name robco-forge-dev --region us-west-2 --query 'cluster.status'

# Check nodes
kubectl get nodes

# Verify all nodes are Ready
kubectl get nodes --no-headers | grep -c " Ready "
```

**Expected:**
- Cluster status: ACTIVE
- All nodes: Ready

### Step 3: Verify Database and Storage

```bash
# Check RDS
aws rds describe-db-instances --region us-west-2 --query "DBInstances[?contains(DBInstanceIdentifier, 'forge')].DBInstanceStatus"

# Check FSx
aws fsx describe-file-systems --region us-west-2 --query "FileSystems[?contains(Tags[?Key=='Name'].Value, 'forge')].Lifecycle"
```

**Expected:**
- RDS status: available
- FSx status: AVAILABLE

### Step 4: Verify Kubernetes Infrastructure

```bash
# Check namespaces
kubectl get namespaces | grep forge

# Check service accounts with IRSA
kubectl get sa -n forge-api
kubectl get sa -n forge-workers
kubectl get sa -n forge-system

# Verify IRSA annotations
kubectl get sa forge-api-sa -n forge-api -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}'
```

**Expected:**
- Namespaces: forge-api, forge-system, forge-workers
- Service accounts with IRSA annotations present

### Step 5: Test Connectivity

```bash
# Test RDS connectivity
kubectl run postgres-test --image=postgres:15-alpine --rm -it --restart=Never -- sh
# Inside pod: nc -zv <rds-endpoint> 5432

# Test FSx connectivity
kubectl run nfs-test --image=busybox --rm -it --restart=Never -- sh
# Inside pod: nc -zv <fsx-dns-name> 2049
```

**Expected:** Both connections successful

## Validation Results

### Success Indicators

✅ **All checks passed when you see:**
- Validation script exits with code 0
- All automated checks show green checkmarks (✓)
- No red X marks (✗) in output
- All manual verification items completed

### Failure Indicators

❌ **Investigation needed if you see:**
- Validation script exits with code 1
- Red X marks (✗) in output
- Yellow warnings (⚠) for critical components
- Terraform outputs missing
- EKS nodes not Ready
- RDS/FSx not accessible

## Troubleshooting

### Common Issues

#### 1. Terraform state not found

**Symptoms:** "Terraform state not found" error

**Solution:**
```bash
cd terraform/environments/dev
terraform init
terraform plan
```

#### 2. kubectl can't connect to cluster

**Symptoms:** "The connection to the server was refused"

**Solution:**
```bash
aws eks update-kubeconfig --name robco-forge-dev --region us-west-2
kubectl cluster-info
```

#### 3. Service accounts missing IRSA annotations

**Symptoms:** Service account exists but no role ARN annotation

**Solution:**
```bash
cd cdk
npm run deploy -- -c environment=dev --all
```

#### 4. RDS/FSx not accessible from EKS

**Symptoms:** Connection timeout or refused

**Solution:**
- Check security group rules
- Verify VPC endpoints
- Check network ACLs
- Review subnet routing tables

#### 5. External Secrets Operator not running

**Symptoms:** ExternalSecrets not syncing

**Solution:**
```bash
cd cdk/k8s-manifests
./deploy-external-secrets.sh
```

## Manual Verification Tasks

After automated validation passes, complete these manual checks:

### 1. WSP-Only Configuration

1. Log into AWS WorkSpaces console
2. Navigate to Directories
3. Select RobCo Forge directory
4. Verify PCoIP is disabled (WSP only)

### 2. Group Policies

Connect to domain controller and verify:
- [ ] Clipboard operations disabled
- [ ] USB device redirection disabled
- [ ] Drive redirection disabled
- [ ] File transfer disabled
- [ ] Printing disabled
- [ ] Screen watermarking enabled

### 3. Active Directory Integration

Test:
- [ ] FSx can join the domain
- [ ] WorkSpaces can join the domain
- [ ] Domain authentication works

## Documentation

### Quick References
- [Quick Start Guide](docs/VALIDATION_QUICK_START.md) - 5-minute validation
- [Validation Script README](scripts/README.md) - Script documentation

### Detailed Guides
- [Infrastructure Validation Checklist](docs/infrastructure-validation-checklist.md) - Complete checklist
- [Phase 1 Checkpoint Summary](docs/phase1-checkpoint-summary.md) - Deployment summary
- [Terraform Deployment Guide](terraform/DEPLOYMENT.md) - Terraform details
- [CDK Deployment Guide](cdk/DEPLOYMENT_GUIDE.md) - Kubernetes details

## Next Steps

After successful validation:

1. ✅ Mark Task 3 as complete in `.kiro/specs/robco-forge/tasks.md`
2. 🚀 Proceed to Phase 2: Core API and Data Layer
3. 📝 Start Task 4: Implement database models and migrations

## Support

Need help?

- **CloudWatch Logs:** `/aws/forge/{environment}/`
- **Terraform State:** `cd terraform/environments/dev && terraform show`
- **kubectl Logs:** `kubectl logs -n <namespace> <pod-name>`
- **Platform Team:** platform-team@robco.com

## Validation Sign-off

Once validation is complete, document:

- **Date:** ___________________
- **Environment:** ___________________
- **Validated by:** ___________________
- **Status:** [ ] Passed [ ] Failed
- **Ready for Phase 2:** [ ] Yes [ ] No

**Notes:**
_____________________________________________
_____________________________________________

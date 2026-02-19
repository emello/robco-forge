# Infrastructure Validation Quick Start Guide

This guide provides a quick reference for validating the RobCo Forge Phase 1 infrastructure.

## Prerequisites

Ensure you have:
- AWS CLI configured with credentials
- kubectl installed
- Terraform installed
- Access to the EKS cluster

## Quick Validation (5 minutes)

### Step 1: Run Automated Validation Script

```bash
# Navigate to project root
cd /path/to/robco-forge

# Make script executable (Linux/Mac only)
chmod +x scripts/validate-infrastructure.sh

# Run validation for dev environment
./scripts/validate-infrastructure.sh dev us-west-2
```

**Expected Output:** All checks should show ✓ (green checkmarks)

### Step 2: Verify Key Components

```bash
# Check Terraform outputs
cd terraform/environments/dev
terraform output

# Check EKS cluster
aws eks describe-cluster --name robco-forge-dev --region us-west-2 --query 'cluster.status'

# Check kubectl access
kubectl get nodes

# Check namespaces
kubectl get namespaces | grep forge

# Check service accounts with IRSA
kubectl get sa -n forge-api
kubectl get sa forge-api-sa -n forge-api -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}'
```

### Step 3: Test Connectivity

```bash
# Test RDS connectivity from EKS
kubectl run postgres-test --image=postgres:15-alpine --rm -it --restart=Never -- sh
# Inside pod: nc -zv <rds-endpoint> 5432

# Test FSx connectivity from EKS
kubectl run nfs-test --image=busybox --rm -it --restart=Never -- sh
# Inside pod: nc -zv <fsx-dns-name> 2049
```

## Validation Checklist (Quick)

- [ ] Terraform state exists and all outputs present
- [ ] EKS cluster is ACTIVE
- [ ] All EKS nodes are Ready
- [ ] RDS instance is available
- [ ] FSx filesystem is AVAILABLE
- [ ] WorkSpaces directory is REGISTERED
- [ ] All namespaces exist (forge-api, forge-system, forge-workers)
- [ ] All service accounts have IRSA annotations
- [ ] RDS is accessible from EKS
- [ ] FSx is accessible from EKS

## Common Commands

### Terraform

```bash
# Check state
cd terraform/environments/dev
terraform state list

# View outputs
terraform output

# Show specific output
terraform output -raw vpc_id
```

### EKS/Kubernetes

```bash
# Update kubeconfig
aws eks update-kubeconfig --name robco-forge-dev --region us-west-2

# Check cluster
kubectl cluster-info

# Check nodes
kubectl get nodes

# Check all resources in namespace
kubectl get all -n forge-api

# Check service account IRSA
kubectl get sa forge-api-sa -n forge-api -o yaml
```

### AWS Resources

```bash
# Check RDS
aws rds describe-db-instances --region us-west-2

# Check FSx
aws fsx describe-file-systems --region us-west-2

# Check WorkSpaces directory
aws workspaces describe-workspace-directories --region us-west-2

# Check CloudWatch log groups
aws logs describe-log-groups --log-group-name-prefix "/aws/forge/" --region us-west-2
```

## Troubleshooting Quick Fixes

### Issue: kubectl can't connect to cluster

```bash
aws eks update-kubeconfig --name robco-forge-dev --region us-west-2
```

### Issue: Service account missing IRSA annotation

```bash
cd cdk
npm run deploy -- -c environment=dev ForgeApiStack-dev
```

### Issue: External Secrets not syncing

```bash
cd cdk/k8s-manifests
./deploy-external-secrets.sh
```

### Issue: Terraform outputs not showing

```bash
cd terraform/environments/dev
terraform refresh
terraform output
```

## Success Criteria

✅ **Infrastructure is ready when:**
- Validation script exits with code 0 (all checks passed)
- All manual verification items completed
- Integration tests successful
- No errors in CloudWatch logs

## Next Steps

After validation passes:
1. Mark Task 3 as complete
2. Proceed to Phase 2: Core API and Data Layer
3. Start Task 4: Implement database models and migrations

## Full Documentation

For detailed information, see:
- [Phase 1 Checkpoint Summary](phase1-checkpoint-summary.md)
- [Infrastructure Validation Checklist](infrastructure-validation-checklist.md)
- [Validation Script README](../scripts/README.md)
- [Terraform Deployment Guide](../terraform/DEPLOYMENT.md)
- [CDK Deployment Guide](../cdk/DEPLOYMENT_GUIDE.md)

## Support

Questions? Check:
- CloudWatch logs: `/aws/forge/dev/`
- Terraform state: `terraform show`
- kubectl logs: `kubectl logs -n <namespace> <pod-name>`
- Platform team: platform-team@robco.com

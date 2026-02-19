# RobCo Forge Infrastructure Validation Scripts

This directory contains scripts for validating the RobCo Forge infrastructure deployment.

## validate-infrastructure.sh

Comprehensive validation script for Phase 1 infrastructure components.

### What it validates:

1. **Terraform Deployment**
   - Terraform state exists
   - All required outputs are present (VPC, EKS, RDS, FSx, WorkSpaces Directory)

2. **EKS Cluster Health**
   - Cluster is in ACTIVE state
   - Nodes are running and Ready
   - kubectl can connect to the cluster

3. **RDS Accessibility**
   - RDS instance is available
   - Network connectivity from EKS to RDS (port 5432)

4. **FSx ONTAP Accessibility**
   - FSx filesystem is AVAILABLE
   - Network connectivity from EKS to FSx (port 2049)

5. **WorkSpaces Directory Configuration**
   - Directory is REGISTERED
   - Configuration is correct (manual verification required for WSP-only)

6. **Kubernetes Infrastructure (CDK)**
   - All namespaces exist (forge-api, forge-system, forge-workers)
   - Service accounts with IRSA annotations are configured
   - External Secrets Operator is running (if deployed)

7. **Monitoring Infrastructure**
   - CloudWatch log groups exist
   - SNS topics are configured

### Usage:

```bash
# Make script executable
chmod +x scripts/validate-infrastructure.sh

# Run validation for dev environment
./scripts/validate-infrastructure.sh dev us-west-2

# Run validation for staging environment
./scripts/validate-infrastructure.sh staging us-west-2

# Run validation for production environment
./scripts/validate-infrastructure.sh production us-west-2
```

### Prerequisites:

- AWS CLI configured with appropriate credentials
- kubectl installed and configured
- Terraform installed
- Access to the EKS cluster

### Exit Codes:

- `0` - All validation checks passed
- `1` - One or more validation checks failed

### Output:

The script provides colored output:
- ✓ (green) - Check passed
- ✗ (red) - Check failed
- ⚠ (yellow) - Warning or manual verification required

### Troubleshooting:

If validation fails:

1. **Terraform state not found**
   - Ensure you're in the correct directory
   - Verify Terraform has been initialized and applied

2. **EKS cluster not accessible**
   - Run: `aws eks update-kubeconfig --name <cluster-name> --region <region>`
   - Verify AWS credentials have EKS access

3. **RDS/FSx not accessible from EKS**
   - Check security group rules
   - Verify VPC endpoints are configured
   - Check network ACLs

4. **Service accounts missing IRSA annotations**
   - Re-deploy CDK stacks
   - Verify OIDC provider is configured for EKS

5. **External Secrets Operator not running**
   - Deploy External Secrets Operator: `cd cdk/k8s-manifests && ./deploy-external-secrets.sh`

### Manual Verification Required:

Some checks require manual verification:

1. **WSP-Only Configuration**
   - Log into AWS WorkSpaces console
   - Navigate to Directories
   - Verify PCoIP is disabled at directory level

2. **Group Policies**
   - Connect to WorkSpaces directory domain controller
   - Verify Group Policies are applied:
     - Clipboard disabled
     - USB redirection disabled
     - Drive mapping disabled
     - Printing disabled
     - Screen watermarking enabled

3. **Active Directory Integration**
   - Verify FSx can join the domain
   - Verify WorkSpaces can join the domain
   - Test domain authentication

### Next Steps:

After all validation checks pass:

1. Proceed to Phase 2: Core API and Data Layer
2. Implement database models and migrations (Task 4)
3. Deploy application services to EKS
4. Configure monitoring dashboards

### Support:

For issues or questions:
- Check CloudWatch logs: `/aws/forge/{environment}/`
- Review Terraform state: `terraform show`
- Check EKS cluster logs: `kubectl logs -n <namespace> <pod-name>`
- Contact platform team: platform-team@robco.com

# RobCo Forge Infrastructure Validation Checklist

This checklist provides a comprehensive guide for validating the Phase 1 infrastructure deployment.

## Automated Validation

Run the automated validation script first:

```bash
./scripts/validate-infrastructure.sh dev us-west-2
```

## Manual Verification Checklist

### 1. Terraform Modules Deployment

- [ ] All Terraform modules applied successfully without errors
- [ ] Terraform state is stored in S3 backend
- [ ] State locking is working (DynamoDB table exists)
- [ ] All required outputs are present:
  - [ ] VPC ID
  - [ ] EKS Cluster Name
  - [ ] RDS Endpoint
  - [ ] FSx DNS Name
  - [ ] WorkSpaces Directory ID
  - [ ] SNS Topic ARN

**Verification Commands:**
```bash
cd terraform/environments/dev
terraform state list
terraform output
```

### 2. Networking Module

- [ ] VPC created with correct CIDR block
- [ ] Private subnets created across 3 availability zones
- [ ] NAT Gateway deployed with egress allowlist
- [ ] VPC Endpoints configured:
  - [ ] S3 VPC Endpoint
  - [ ] Secrets Manager VPC Endpoint
  - [ ] FSx VPC Endpoint
- [ ] Security groups configured with least-privilege rules
- [ ] No direct internet access for WorkSpaces VPC

**Verification Commands:**
```bash
# Check VPC
aws ec2 describe-vpcs --vpc-ids <vpc-id>

# Check subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=<vpc-id>"

# Check NAT Gateway
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=<vpc-id>"

# Check VPC Endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=<vpc-id>"
```

### 3. EKS Cluster Module

- [ ] EKS cluster is ACTIVE
- [ ] Cluster spans 3 availability zones
- [ ] Private API endpoint configured
- [ ] Node groups deployed in private subnets
- [ ] IAM roles for service accounts (IRSA) configured
- [ ] OIDC provider exists and is associated with cluster
- [ ] Cluster logging enabled to CloudWatch
- [ ] All nodes are Ready

**Verification Commands:**
```bash
# Check cluster status
aws eks describe-cluster --name <cluster-name>

# Check OIDC provider
aws eks describe-cluster --name <cluster-name> --query 'cluster.identity.oidc.issuer'
aws iam list-open-id-connect-providers

# Check nodes
kubectl get nodes
kubectl describe nodes
```

### 4. RDS PostgreSQL Module

- [ ] RDS instance is available
- [ ] Multi-AZ deployment enabled
- [ ] Encryption at rest enabled (AES-256)
- [ ] Automated backups configured (daily, 30-day retention)
- [ ] Read replica created for cost queries
- [ ] Connection pooling configured (PgBouncer)
- [ ] Security group allows only EKS pods
- [ ] Accessible from EKS cluster

**Verification Commands:**
```bash
# Check RDS instance
aws rds describe-db-instances --db-instance-identifier <instance-id>

# Check encryption
aws rds describe-db-instances --db-instance-identifier <instance-id> --query 'DBInstances[0].StorageEncrypted'

# Check backups
aws rds describe-db-instances --db-instance-identifier <instance-id> --query 'DBInstances[0].BackupRetentionPeriod'

# Test connectivity from EKS (run from a pod)
kubectl run -it --rm postgres-test --image=postgres:15-alpine --restart=Never -- psql -h <rds-endpoint> -U <username> -d postgres
```

### 5. FSx ONTAP Module

- [ ] FSx filesystem is AVAILABLE
- [ ] Encryption at rest enabled (AES-256)
- [ ] Automated backups configured (daily, 30-day retention)
- [ ] Deduplication and compression enabled
- [ ] SVM created for user volumes
- [ ] Accessible from EKS cluster
- [ ] Active Directory integration configured

**Verification Commands:**
```bash
# Check FSx filesystem
aws fsx describe-file-systems

# Check encryption
aws fsx describe-file-systems --query 'FileSystems[0].OntapConfiguration.DiskIopsConfiguration'

# Check backups
aws fsx describe-backups --filters "Name=file-system-id,Values=<filesystem-id>"

# Test NFS mount from EKS (run from a pod)
kubectl run -it --rm nfs-test --image=busybox --restart=Never -- nc -zv <fsx-dns-name> 2049
```

### 6. WorkSpaces Directory Module

- [ ] WorkSpaces directory is REGISTERED
- [ ] Active Directory integration configured
- [ ] PCoIP disabled at directory level (WSP-only)
- [ ] Domain join configuration set up
- [ ] Group Policies configured for data exfiltration prevention:
  - [ ] Clipboard operations disabled
  - [ ] USB device redirection disabled
  - [ ] Drive redirection disabled
  - [ ] File transfer disabled
  - [ ] Printing disabled
  - [ ] Screen watermarking enabled

**Verification Commands:**
```bash
# Check directory status
aws workspaces describe-workspace-directories --directory-ids <directory-id>

# Check streaming properties
aws workspaces describe-workspace-directories --directory-ids <directory-id> --query 'Directories[0].WorkspaceCreationProperties'
```

**Manual Verification (AWS Console):**
1. Navigate to AWS WorkSpaces console
2. Go to Directories
3. Select the RobCo Forge directory
4. Verify:
   - Status is "Registered"
   - Streaming protocol is WSP only (PCoIP disabled)
   - Group Policies are applied

### 7. Monitoring Module

- [ ] CloudWatch log groups created with retention policies
- [ ] Prometheus deployment on EKS (if deployed)
- [ ] Grafana deployment on EKS (if deployed)
- [ ] CloudWatch alarms configured for critical metrics
- [ ] SNS topics configured for alerts
- [ ] Alert email subscriptions confirmed

**Verification Commands:**
```bash
# Check CloudWatch log groups
aws logs describe-log-groups --log-group-name-prefix "/aws/forge/"

# Check SNS topics
aws sns list-topics | grep forge

# Check SNS subscriptions
aws sns list-subscriptions-by-topic --topic-arn <topic-arn>

# Check CloudWatch alarms
aws cloudwatch describe-alarms --alarm-name-prefix "forge-"
```

### 8. Kubernetes Infrastructure (CDK)

- [ ] All CDK stacks deployed successfully
- [ ] Namespaces created:
  - [ ] forge-api
  - [ ] forge-system
  - [ ] forge-workers
- [ ] Service accounts with IRSA annotations:
  - [ ] forge-api-sa (forge-api namespace)
  - [ ] forge-lucy-sa (forge-api namespace)
  - [ ] forge-cost-engine-sa (forge-workers namespace)
  - [ ] prometheus-sa (forge-system namespace)
  - [ ] grafana-sa (forge-system namespace)
- [ ] RBAC roles and bindings configured
- [ ] Network policies applied

**Verification Commands:**
```bash
# Check namespaces
kubectl get namespaces | grep forge

# Check service accounts
kubectl get sa -n forge-api
kubectl get sa -n forge-workers
kubectl get sa -n forge-system

# Check IRSA annotations
kubectl get sa forge-api-sa -n forge-api -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}'

# Check RBAC
kubectl get roles,rolebindings -n forge-api
kubectl get clusterroles,clusterrolebindings | grep forge

# Check network policies
kubectl get networkpolicies -A
```

### 9. Secrets Management

- [ ] External Secrets Operator deployed
- [ ] SecretStore configured for AWS Secrets Manager
- [ ] ExternalSecrets created for:
  - [ ] RDS credentials
  - [ ] Okta SSO credentials
  - [ ] Anthropic API key
  - [ ] Redis credentials
  - [ ] Grafana admin credentials
  - [ ] JWT signing key
- [ ] All ExternalSecrets synced successfully
- [ ] Kubernetes Secrets created from ExternalSecrets

**Verification Commands:**
```bash
# Check External Secrets Operator
kubectl get pods -n external-secrets

# Check SecretStores
kubectl get secretstores -A

# Check ExternalSecrets
kubectl get externalsecrets -A

# Check synced Kubernetes Secrets
kubectl get secrets -n forge-api | grep forge
kubectl get secrets -n forge-workers | grep forge
kubectl get secrets -n forge-system | grep grafana
```

## Integration Tests

### Test 1: EKS to RDS Connectivity

```bash
# Create test pod
kubectl run postgres-test --image=postgres:15-alpine --rm -it --restart=Never -- sh

# Inside pod, test connection
nc -zv <rds-endpoint> 5432
```

Expected: Connection successful

### Test 2: EKS to FSx Connectivity

```bash
# Create test pod
kubectl run nfs-test --image=busybox --rm -it --restart=Never -- sh

# Inside pod, test NFS port
nc -zv <fsx-dns-name> 2049
```

Expected: Connection successful

### Test 3: IRSA Functionality

```bash
# Create test pod with service account
kubectl run aws-cli-test --image=amazon/aws-cli --rm -it --restart=Never \
  --serviceaccount=forge-api-sa -n forge-api -- sts get-caller-identity
```

Expected: Should return IAM role ARN (not user credentials)

### Test 4: External Secrets Sync

```bash
# Check ExternalSecret status
kubectl describe externalsecret forge-api-db-credentials -n forge-api
```

Expected: Status should show "SecretSynced" with no errors

## Sign-off

Once all checks pass, complete this sign-off:

- [ ] All automated validation checks passed
- [ ] All manual verification checks completed
- [ ] All integration tests successful
- [ ] Infrastructure is ready for Phase 2 deployment

**Validated by:** ___________________  
**Date:** ___________________  
**Environment:** ___________________  

## Troubleshooting

If any checks fail, refer to:
- `terraform/DEPLOYMENT.md` - Terraform deployment guide
- `cdk/DEPLOYMENT_GUIDE.md` - CDK deployment guide
- `scripts/README.md` - Validation script documentation
- CloudWatch logs: `/aws/forge/{environment}/`

## Next Steps

After validation:
1. Proceed to Phase 2: Core API and Data Layer
2. Implement database models and migrations (Task 4)
3. Deploy Forge API services
4. Configure monitoring dashboards

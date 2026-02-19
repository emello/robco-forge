# RobCo Forge Kubernetes Infrastructure Deployment Guide

This guide provides step-by-step instructions for deploying the Kubernetes infrastructure for RobCo Forge.

## Overview

The deployment consists of three main components:

1. **AWS CDK Stacks** - Creates service accounts with IRSA for AWS access
2. **Kubernetes Manifests** - Creates namespaces, RBAC, and network policies
3. **External Secrets Operator** - Synchronizes secrets from AWS Secrets Manager

## Prerequisites

- AWS CLI configured with appropriate credentials
- kubectl configured to access the EKS cluster
- Helm 3.x installed
- Node.js 18+ and npm installed
- EKS cluster already deployed via Terraform (Task 1)

## Deployment Steps

### Step 1: Configure Environment

Update `cdk.context.json` with your environment-specific values:

```bash
cd cdk
cp cdk.context.json cdk.context.json.example
```

Edit `cdk.context.json` and replace placeholders:
- `REPLACE_WITH_DEV_ACCOUNT_ID` - Your AWS account ID
- `REPLACE_WITH_VPC_ID` - VPC ID from Terraform output
- `REPLACE_WITH_EKS_CLUSTER_ARN` - EKS cluster ARN
- `REPLACE_WITH_OIDC_PROVIDER_ARN` - OIDC provider ARN
- `REPLACE_WITH_SECRETS_MANAGER_ARN` - Secrets Manager ARN pattern

### Step 2: Install CDK Dependencies

```bash
cd cdk
npm install
npm run build
```

### Step 3: Deploy CDK Stacks

Deploy all stacks to create service accounts with IRSA:

```bash
# Deploy to dev environment
npm run deploy -- -c environment=dev --all

# Or deploy individual stacks
npm run deploy -- -c environment=dev ForgeApiStack-dev
npm run deploy -- -c environment=dev ForgeLucyStack-dev
npm run deploy -- -c environment=dev ForgeCostEngineStack-dev
npm run deploy -- -c environment=dev ForgeMonitoringStack-dev
```

Verify CDK deployment:

```bash
aws cloudformation describe-stacks --stack-name ForgeApiStack-dev
```

### Step 4: Configure kubectl

Ensure kubectl is configured to access your EKS cluster:

```bash
aws eks update-kubeconfig --name robco-forge-dev --region us-west-2
kubectl cluster-info
```

### Step 5: Deploy Kubernetes Manifests

Deploy namespaces, RBAC, and network policies:

```bash
cd k8s-manifests

# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

Or manually apply:

```bash
kubectl apply -f namespaces.yaml
kubectl apply -f rbac.yaml
kubectl apply -f network-policies.yaml
```

Verify deployment:

```bash
# Check namespaces
kubectl get namespaces | grep forge

# Check service accounts (created by CDK)
kubectl get sa -n forge-api
kubectl get sa -n forge-workers
kubectl get sa -n forge-system

# Check RBAC
kubectl get roles,rolebindings -n forge-api
kubectl get clusterroles,clusterrolebindings | grep forge

# Check network policies
kubectl get networkpolicies -n forge-api
```

### Step 6: Create AWS Secrets Manager Secrets

Create required secrets in AWS Secrets Manager:

```bash
# RDS credentials
aws secretsmanager create-secret \
  --name robco-forge/rds/credentials \
  --secret-string '{
    "username": "forge_admin",
    "password": "SECURE_PASSWORD_HERE",
    "host": "robco-forge-db.cluster-xxxxx.us-west-2.rds.amazonaws.com",
    "port": "5432",
    "database": "forge"
  }'

# Okta SSO credentials
aws secretsmanager create-secret \
  --name robco-forge/okta/credentials \
  --secret-string '{
    "client_id": "OKTA_CLIENT_ID",
    "client_secret": "OKTA_CLIENT_SECRET",
    "issuer": "https://robco.okta.com",
    "redirect_uri": "https://forge.robco.com/auth/callback"
  }'

# Anthropic API key
aws secretsmanager create-secret \
  --name robco-forge/anthropic/api-key \
  --secret-string '{
    "api_key": "sk-ant-YOUR_KEY_HERE"
  }'

# Redis credentials
aws secretsmanager create-secret \
  --name robco-forge/redis/credentials \
  --secret-string '{
    "host": "robco-forge-redis.xxxxx.cache.amazonaws.com",
    "port": "6379"
  }'

# Grafana admin credentials
aws secretsmanager create-secret \
  --name robco-forge/grafana/admin \
  --secret-string '{
    "username": "admin",
    "password": "SECURE_PASSWORD_HERE"
  }'

# JWT signing key
JWT_KEY=$(openssl rand -base64 32)
aws secretsmanager create-secret \
  --name robco-forge/jwt/signing-key \
  --secret-string "{\"signing_key\": \"$JWT_KEY\"}"
```

### Step 7: Deploy External Secrets Operator

Deploy External Secrets Operator to synchronize secrets:

```bash
cd k8s-manifests

# Make deployment script executable
chmod +x deploy-external-secrets.sh

# Run deployment
./deploy-external-secrets.sh
```

Or manually deploy:

```bash
# Add Helm repository
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

# Install External Secrets Operator
helm upgrade --install external-secrets \
  external-secrets/external-secrets \
  --namespace external-secrets \
  --create-namespace \
  --set installCRDs=true \
  --set serviceAccount.create=false \
  --set serviceAccount.name=external-secrets-sa \
  --wait

# Apply manifests
kubectl apply -f external-secrets-operator.yaml
kubectl apply -f secret-stores.yaml
kubectl apply -f external-secrets.yaml
```

Verify External Secrets Operator:

```bash
# Check operator pods
kubectl get pods -n external-secrets

# Check ExternalSecrets status
kubectl get externalsecrets -A

# Check synced Kubernetes Secrets
kubectl get secrets -n forge-api | grep forge
kubectl get secrets -n forge-workers | grep forge
kubectl get secrets -n forge-system | grep grafana
```

### Step 8: Verify End-to-End

Verify the complete setup:

```bash
# Check all namespaces
kubectl get namespaces | grep forge

# Check all service accounts have IRSA annotations
kubectl get sa forge-api-sa -n forge-api -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}'
kubectl get sa forge-lucy-sa -n forge-api -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}'
kubectl get sa forge-cost-engine-sa -n forge-workers -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}'
kubectl get sa prometheus-sa -n forge-system -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}'
kubectl get sa grafana-sa -n forge-system -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}'

# Check all secrets are synced
kubectl get externalsecrets -A -o wide

# Check network policies are applied
kubectl get networkpolicies -A
```

## Deployment to Other Environments

### Staging

```bash
# Update cdk.context.json with staging values
# Deploy CDK stacks
cd cdk
npm run deploy -- -c environment=staging --all

# Deploy Kubernetes manifests
cd k8s-manifests
./deploy.sh

# Deploy External Secrets Operator
./deploy-external-secrets.sh
```

### Production

```bash
# Update cdk.context.json with production values
# Deploy CDK stacks (requires approval)
cd cdk
npm run deploy -- -c environment=production --all

# Deploy Kubernetes manifests
cd k8s-manifests
./deploy.sh

# Deploy External Secrets Operator
./deploy-external-secrets.sh
```

## Troubleshooting

### CDK Deployment Fails

**Issue**: Stack deployment fails with "Cluster not found"

**Solution**: Verify EKS cluster exists and OIDC provider is configured:

```bash
aws eks describe-cluster --name robco-forge-dev
aws iam list-open-id-connect-providers
```

### Service Account Missing IRSA Annotation

**Issue**: Service account doesn't have `eks.amazonaws.com/role-arn` annotation

**Solution**: Re-deploy CDK stack:

```bash
cd cdk
npm run deploy -- -c environment=dev ForgeApiStack-dev
```

### ExternalSecret Not Syncing

**Issue**: ExternalSecret shows "SecretSyncedError"

**Solution**: Check the ExternalSecret status:

```bash
kubectl describe externalsecret forge-api-db-credentials -n forge-api
```

Common causes:
- Secret doesn't exist in AWS Secrets Manager
- IRSA role doesn't have permission to access secret
- SecretStore configuration is incorrect

### Network Policy Blocking Traffic

**Issue**: Pods can't communicate with each other

**Solution**: Temporarily disable network policies for debugging:

```bash
kubectl delete networkpolicy forge-api-network-policy -n forge-api
```

Test connectivity, then re-apply:

```bash
kubectl apply -f network-policies.yaml
```

### Permission Denied Errors

**Issue**: Pods can't access AWS services

**Solution**: Verify IRSA is working:

```bash
# Check service account annotation
kubectl get sa forge-api-sa -n forge-api -o yaml

# Check IAM role trust policy
aws iam get-role --role-name <role-name-from-annotation>

# Check CloudTrail for denied API calls
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRoleWithWebIdentity \
  --max-results 10
```

## Rollback Procedures

### Rollback CDK Stacks

```bash
cd cdk
npm run destroy -- -c environment=dev --all
```

### Rollback Kubernetes Manifests

```bash
cd k8s-manifests
kubectl delete -f external-secrets.yaml
kubectl delete -f secret-stores.yaml
kubectl delete -f network-policies.yaml
kubectl delete -f rbac.yaml
kubectl delete -f namespaces.yaml
```

### Rollback External Secrets Operator

```bash
helm uninstall external-secrets -n external-secrets
kubectl delete namespace external-secrets
```

## Next Steps

After completing this deployment:

1. **Deploy Application Services** (Phase 2)
   - Deploy Forge API Helm chart
   - Deploy Lucy AI service Helm chart
   - Deploy Cost Engine Helm chart

2. **Deploy Monitoring** (Phase 9)
   - Deploy Prometheus
   - Deploy Grafana
   - Configure dashboards

3. **Verify End-to-End**
   - Test API endpoints
   - Test Lucy AI integration
   - Test cost tracking
   - Verify monitoring and alerting

## References

- [CDK README](README.md)
- [Kubernetes Manifests README](k8s-manifests/README.md)
- [Secrets Management Guide](k8s-manifests/SECRETS_MANAGEMENT.md)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [External Secrets Operator](https://external-secrets.io/)

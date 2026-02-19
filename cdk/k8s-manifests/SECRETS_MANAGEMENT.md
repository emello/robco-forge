# Secrets Management with External Secrets Operator

This document describes the secrets management setup for RobCo Forge using External Secrets Operator (ESO).

## Overview

RobCo Forge uses External Secrets Operator to synchronize secrets from AWS Secrets Manager into Kubernetes Secrets. This approach provides:

- **Centralized Secret Management**: All secrets stored in AWS Secrets Manager
- **Automatic Rotation**: Secrets automatically updated in Kubernetes when rotated in AWS
- **IRSA Integration**: No credentials stored in Kubernetes
- **Audit Trail**: All secret access logged in CloudTrail

## Architecture

```
AWS Secrets Manager
        ↓
External Secrets Operator (with IRSA)
        ↓
Kubernetes Secrets
        ↓
Application Pods
```

## Components

### 1. External Secrets Operator

Deployed in the `external-secrets` namespace with:
- Service account with IRSA for AWS Secrets Manager access
- ClusterRole for managing ExternalSecret CRDs
- Deployment running the operator controller

### 2. SecretStores

SecretStores define how to access AWS Secrets Manager:

- **ClusterSecretStore**: `aws-secrets-manager` (cluster-wide)
- **SecretStore**: Namespace-scoped stores for each namespace

### 3. ExternalSecrets

ExternalSecret resources define which secrets to sync:

- `forge-api-db-credentials` - RDS database credentials
- `forge-api-okta-credentials` - Okta SSO credentials
- `forge-lucy-anthropic-key` - Anthropic API key
- `forge-api-redis-credentials` - Redis connection credentials
- `forge-cost-engine-db-credentials` - Cost Engine database credentials
- `grafana-admin-credentials` - Grafana admin credentials
- `forge-api-jwt-key` - JWT signing key

## Prerequisites

1. AWS Secrets Manager secrets created
2. EKS cluster with OIDC provider
3. External Secrets Operator Helm chart installed

## Installation

### Step 1: Install External Secrets Operator

```bash
# Add External Secrets Operator Helm repository
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

# Install External Secrets Operator
helm install external-secrets \
  external-secrets/external-secrets \
  --namespace external-secrets \
  --create-namespace \
  --set installCRDs=true \
  --set serviceAccount.create=false \
  --set serviceAccount.name=external-secrets-sa
```

### Step 2: Create IRSA for External Secrets Operator

Deploy the CDK stack or manually create IAM role:

```bash
cd ../
npm run deploy -- -c environment=dev ExternalSecretsStack-dev
```

Or manually annotate the service account:

```bash
kubectl annotate serviceaccount external-secrets-sa \
  -n external-secrets \
  eks.amazonaws.com/role-arn=arn:aws:iam::ACCOUNT_ID:role/external-secrets-role
```

### Step 3: Apply Kubernetes Manifests

```bash
# Apply External Secrets Operator RBAC
kubectl apply -f external-secrets-operator.yaml

# Apply SecretStores
kubectl apply -f secret-stores.yaml

# Apply ExternalSecrets
kubectl apply -f external-secrets.yaml
```

## AWS Secrets Manager Setup

### Required Secrets

Create the following secrets in AWS Secrets Manager:

#### 1. RDS Database Credentials

```bash
aws secretsmanager create-secret \
  --name robco-forge/rds/credentials \
  --description "RDS PostgreSQL credentials for RobCo Forge" \
  --secret-string '{
    "username": "forge_admin",
    "password": "REPLACE_WITH_SECURE_PASSWORD",
    "host": "robco-forge-db.cluster-xxxxx.us-west-2.rds.amazonaws.com",
    "port": "5432",
    "database": "forge"
  }'
```

#### 2. Okta SSO Credentials

```bash
aws secretsmanager create-secret \
  --name robco-forge/okta/credentials \
  --description "Okta SSO credentials for RobCo Forge" \
  --secret-string '{
    "client_id": "OKTA_CLIENT_ID",
    "client_secret": "OKTA_CLIENT_SECRET",
    "issuer": "https://robco.okta.com",
    "redirect_uri": "https://forge.robco.com/auth/callback"
  }'
```

#### 3. Anthropic API Key

```bash
aws secretsmanager create-secret \
  --name robco-forge/anthropic/api-key \
  --description "Anthropic Claude API key for Lucy AI" \
  --secret-string '{
    "api_key": "sk-ant-REPLACE_WITH_ACTUAL_KEY"
  }'
```

#### 4. Redis Credentials

```bash
aws secretsmanager create-secret \
  --name robco-forge/redis/credentials \
  --description "Redis/ElastiCache credentials for RobCo Forge" \
  --secret-string '{
    "host": "robco-forge-redis.xxxxx.cache.amazonaws.com",
    "port": "6379"
  }'
```

#### 5. Grafana Admin Credentials

```bash
aws secretsmanager create-secret \
  --name robco-forge/grafana/admin \
  --description "Grafana admin credentials" \
  --secret-string '{
    "username": "admin",
    "password": "REPLACE_WITH_SECURE_PASSWORD"
  }'
```

#### 6. JWT Signing Key

```bash
# Generate a secure random key
JWT_KEY=$(openssl rand -base64 32)

aws secretsmanager create-secret \
  --name robco-forge/jwt/signing-key \
  --description "JWT signing key for RobCo Forge API" \
  --secret-string "{
    \"signing_key\": \"$JWT_KEY\"
  }"
```

## Secret Rotation

### Automatic Rotation

External Secrets Operator automatically refreshes secrets based on `refreshInterval`:

- Database credentials: Every 1 hour
- API keys: Every 24 hours
- JWT keys: Every 24 hours

### Manual Rotation

To manually rotate a secret:

1. Update the secret in AWS Secrets Manager
2. Wait for the refresh interval, or force refresh:

```bash
# Force refresh by deleting the Kubernetes secret
kubectl delete secret forge-api-db-credentials -n forge-api

# External Secrets Operator will recreate it immediately
kubectl get secret forge-api-db-credentials -n forge-api
```

### Rotation Strategy

For zero-downtime rotation:

1. Update secret in AWS Secrets Manager
2. Wait for External Secrets Operator to sync (up to refresh interval)
3. Restart pods to pick up new secret:

```bash
kubectl rollout restart deployment forge-api -n forge-api
```

## Verification

### Check External Secrets Operator Status

```bash
# Check operator pods
kubectl get pods -n external-secrets

# Check operator logs
kubectl logs -n external-secrets -l app.kubernetes.io/name=external-secrets
```

### Check SecretStores

```bash
# Check ClusterSecretStore
kubectl get clustersecretstore

# Check namespace-scoped SecretStores
kubectl get secretstore -n forge-api
kubectl get secretstore -n forge-workers
kubectl get secretstore -n forge-system
```

### Check ExternalSecrets

```bash
# Check ExternalSecret status
kubectl get externalsecrets -n forge-api
kubectl get externalsecrets -n forge-workers
kubectl get externalsecrets -n forge-system

# Describe an ExternalSecret for details
kubectl describe externalsecret forge-api-db-credentials -n forge-api
```

### Check Synced Kubernetes Secrets

```bash
# Check that secrets were created
kubectl get secrets -n forge-api | grep forge
kubectl get secrets -n forge-workers | grep forge
kubectl get secrets -n forge-system | grep grafana

# View secret data (base64 encoded)
kubectl get secret forge-api-db-credentials -n forge-api -o yaml
```

### Test Secret Access from Pod

```bash
# Create a test pod
kubectl run -it --rm debug \
  --image=busybox \
  --restart=Never \
  -n forge-api \
  -- sh

# Inside the pod, check if secret is mounted
ls /var/run/secrets/kubernetes.io/serviceaccount/
```

## Troubleshooting

### ExternalSecret Not Syncing

Check the ExternalSecret status:

```bash
kubectl describe externalsecret forge-api-db-credentials -n forge-api
```

Common issues:
- **SecretStore not found**: Ensure SecretStore is created in the same namespace
- **Permission denied**: Check IRSA role has access to AWS Secrets Manager
- **Secret not found in AWS**: Verify secret exists in AWS Secrets Manager

### IRSA Not Working

Check service account annotation:

```bash
kubectl get sa external-secrets-sa -n external-secrets -o yaml
```

Verify IAM role trust policy:

```bash
aws iam get-role --role-name external-secrets-role
```

Check CloudTrail for denied API calls:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=GetSecretValue \
  --max-results 10
```

### Secret Not Updating After Rotation

Force refresh:

```bash
# Delete the Kubernetes secret
kubectl delete secret forge-api-db-credentials -n forge-api

# Check ExternalSecret recreates it
kubectl get secret forge-api-db-credentials -n forge-api -w
```

Restart pods to pick up new secret:

```bash
kubectl rollout restart deployment forge-api -n forge-api
```

## Security Best Practices

### 1. Least Privilege IAM Policies

Grant only necessary permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-west-2:123456789012:secret:robco-forge/*"
    }
  ]
}
```

### 2. Namespace Isolation

Use namespace-scoped SecretStores to limit secret access:

- `forge-api-secret-store` only accessible from `forge-api` namespace
- `forge-workers-secret-store` only accessible from `forge-workers` namespace

### 3. Secret Rotation

Rotate secrets regularly:
- Database credentials: Every 90 days
- API keys: Every 180 days
- JWT signing keys: Every 365 days

### 4. Audit Logging

Enable CloudTrail logging for Secrets Manager:

```bash
aws cloudtrail create-trail \
  --name robco-forge-secrets-audit \
  --s3-bucket-name robco-forge-audit-logs
```

### 5. Encryption at Rest

Use KMS encryption for secrets:

```bash
aws secretsmanager create-secret \
  --name robco-forge/example \
  --kms-key-id arn:aws:kms:us-west-2:123456789012:key/xxxxx \
  --secret-string '{"key": "value"}'
```

## References

- [External Secrets Operator Documentation](https://external-secrets.io/)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [EKS IRSA](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)

## Next Steps

After setting up secrets management:

1. Deploy application Helm charts that reference these secrets
2. Configure secret rotation policies in AWS Secrets Manager
3. Set up CloudWatch alarms for secret access failures
4. Document secret rotation procedures for operations team

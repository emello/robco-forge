# RobCo Forge - AWS CDK Infrastructure

This directory contains AWS CDK infrastructure code for deploying Kubernetes resources to the RobCo Forge EKS cluster.

## Overview

The CDK project deploys the following stacks:

1. **ForgeApiStack** - Forge API services namespace, service accounts, and RBAC
2. **ForgeLucyStack** - Lucy AI service with Bedrock/Claude access
3. **ForgeCostEngineStack** - Cost Engine with Cost Explorer and CloudWatch access
4. **ForgeMonitoringStack** - Prometheus and Grafana with observability permissions

## Prerequisites

- Node.js 18+ and npm
- AWS CLI configured with appropriate credentials
- EKS cluster already deployed (via Terraform)
- AWS CDK CLI installed: `npm install -g aws-cdk`

## Project Structure

```
cdk/
├── bin/
│   └── app.ts                 # CDK app entry point
├── lib/
│   ├── interfaces/
│   │   └── stack-props.ts     # Common stack interfaces
│   └── stacks/
│       ├── forge-api-stack.ts
│       ├── forge-lucy-stack.ts
│       ├── forge-cost-engine-stack.ts
│       └── forge-monitoring-stack.ts
├── cdk.json                   # CDK configuration
├── cdk.context.json           # Environment-specific configuration
├── package.json
└── tsconfig.json
```

## Configuration

### Environment Setup

Before deploying, update `cdk.context.json` with your environment-specific values:

```json
{
  "environments": {
    "dev": {
      "account": "123456789012",
      "region": "us-west-2",
      "clusterName": "robco-forge-dev",
      "vpcId": "vpc-xxxxx",
      "eksClusterArn": "arn:aws:eks:...",
      "eksOidcProviderArn": "arn:aws:iam::...",
      "namespace": {
        "api": "forge-api",
        "system": "forge-system",
        "workers": "forge-workers"
      },
      "secretsManagerArn": "arn:aws:secretsmanager:..."
    }
  }
}
```

### Getting EKS Cluster Information

After deploying the Terraform EKS module, retrieve the required values:

```bash
# Get EKS cluster ARN
aws eks describe-cluster --name robco-forge-dev --query 'cluster.arn' --output text

# Get OIDC provider ARN
aws eks describe-cluster --name robco-forge-dev --query 'cluster.identity.oidc.issuer' --output text
# Then find the provider ARN in IAM console or use:
aws iam list-open-id-connect-providers
```

## Installation

```bash
cd cdk
npm install
```

## Usage

### Build TypeScript

```bash
npm run build
```

### Synthesize CloudFormation Templates

```bash
# For dev environment
npm run synth -- -c environment=dev

# For staging environment
npm run synth -- -c environment=staging

# For production environment
npm run synth -- -c environment=production
```

### Deploy Stacks

```bash
# Deploy all stacks to dev
npm run deploy -- -c environment=dev --all

# Deploy specific stack to dev
npm run deploy -- -c environment=dev ForgeApiStack-dev

# Deploy to staging (requires approval)
npm run deploy -- -c environment=staging --all

# Deploy to production (requires approval)
npm run deploy -- -c environment=production --all
```

### View Differences

```bash
# Compare deployed stack with local changes
npm run diff -- -c environment=dev
```

### Destroy Stacks

```bash
# Destroy all stacks in dev
npm run destroy -- -c environment=dev --all

# Destroy specific stack
npm run destroy -- -c environment=dev ForgeApiStack-dev
```

## Stack Details

### ForgeApiStack

Creates Kubernetes resources for the Forge API service:

- **Namespace**: `forge-api`
- **Service Account**: `forge-api-sa` with IRSA
- **IAM Permissions**:
  - AWS Secrets Manager (read secrets)
  - RDS (describe instances)
  - WorkSpaces API (full management)
  - CloudWatch (metrics)

### ForgeLucyStack

Creates Kubernetes resources for Lucy AI service:

- **Namespace**: `forge-api` (shared with API)
- **Service Account**: `forge-lucy-sa` with IRSA
- **IAM Permissions**:
  - AWS Bedrock (invoke Claude models)
  - AWS Secrets Manager (read secrets)
  - CloudWatch (metrics and logs)
  - ElastiCache (describe clusters)

### ForgeCostEngineStack

Creates Kubernetes resources for Cost Engine:

- **Namespace**: `forge-workers`
- **Service Account**: `forge-cost-engine-sa` with IRSA
- **IAM Permissions**:
  - AWS Cost Explorer (cost data)
  - CloudWatch (metrics)
  - WorkSpaces API (utilization data)
  - Pricing API (pricing data)
  - AWS Secrets Manager (read secrets)

### ForgeMonitoringStack

Creates Kubernetes resources for monitoring:

- **Namespace**: `forge-system`
- **Service Accounts**:
  - `prometheus-sa` with IRSA
  - `grafana-sa` with IRSA
- **IAM Permissions**:
  - CloudWatch (metrics, logs, alarms)
  - X-Ray (distributed tracing)
  - EKS (cluster discovery)

## IRSA (IAM Roles for Service Accounts)

All service accounts use IRSA to assume IAM roles without storing credentials. The CDK automatically:

1. Creates IAM roles with trust relationships to the EKS OIDC provider
2. Attaches IAM policies with least-privilege permissions
3. Annotates Kubernetes service accounts with the IAM role ARN

Pods using these service accounts automatically receive temporary AWS credentials.

## Outputs

Each stack exports CloudFormation outputs:

- Service account names
- Namespace names
- IAM role ARNs

These outputs can be referenced by Helm charts or Kubernetes manifests.

## Next Steps

After deploying the CDK stacks:

1. Deploy Kubernetes manifests for namespaces and RBAC (Task 2.2)
2. Deploy External Secrets Operator for secrets management (Task 2.3)
3. Deploy application Helm charts using the created service accounts

## Troubleshooting

### Stack Deployment Fails

- Verify EKS cluster is running: `aws eks describe-cluster --name <cluster-name>`
- Verify OIDC provider exists: `aws iam list-open-id-connect-providers`
- Check AWS credentials: `aws sts get-caller-identity`

### Service Account Not Working

- Verify IRSA annotation: `kubectl describe sa <service-account> -n <namespace>`
- Check IAM role trust policy includes EKS OIDC provider
- Verify pod has correct service account: `kubectl get pod <pod-name> -n <namespace> -o yaml`

### Permission Denied Errors

- Review IAM role policies: `aws iam get-role-policy --role-name <role-name> --policy-name <policy-name>`
- Check CloudTrail for denied API calls
- Verify least-privilege permissions are sufficient

## References

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [EKS Best Practices - IRSA](https://aws.github.io/aws-eks-best-practices/security/docs/iam/#iam-roles-for-service-accounts-irsa)
- [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)

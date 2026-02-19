# Kubernetes Manifests for RobCo Forge

This directory contains Kubernetes manifests for namespaces, RBAC, and network policies.

## Overview

The manifests are organized as follows:

- **namespaces.yaml** - Creates three namespaces: `forge-api`, `forge-system`, `forge-workers`
- **rbac.yaml** - Creates Roles, RoleBindings, ClusterRoles, and ClusterRoleBindings
- **network-policies.yaml** - Creates NetworkPolicies for pod-to-pod communication control

## Prerequisites

- EKS cluster deployed and accessible via kubectl
- AWS CDK stacks deployed (creates service accounts with IRSA)
- kubectl configured to access the cluster

## Deployment Order

Apply manifests in the following order:

1. Namespaces (creates the namespaces)
2. RBAC (creates roles and bindings)
3. Network Policies (restricts network traffic)

## Quick Start

```bash
# Set your kubeconfig context
export KUBECONFIG=~/.kube/config
aws eks update-kubeconfig --name robco-forge-dev --region us-west-2

# Apply all manifests
kubectl apply -f namespaces.yaml
kubectl apply -f rbac.yaml
kubectl apply -f network-policies.yaml
```

## Verification

### Verify Namespaces

```bash
kubectl get namespaces | grep forge
```

Expected output:
```
forge-api       Active   1m
forge-system    Active   1m
forge-workers   Active   1m
```

### Verify RBAC

```bash
# Check roles
kubectl get roles -n forge-api
kubectl get roles -n forge-workers
kubectl get roles -n forge-system

# Check role bindings
kubectl get rolebindings -n forge-api
kubectl get rolebindings -n forge-workers
kubectl get rolebindings -n forge-system

# Check cluster roles
kubectl get clusterroles | grep prometheus

# Check cluster role bindings
kubectl get clusterrolebindings | grep prometheus
```

### Verify Network Policies

```bash
kubectl get networkpolicies -n forge-api
kubectl get networkpolicies -n forge-workers
kubectl get networkpolicies -n forge-system
```

### Verify Service Accounts (created by CDK)

```bash
# Check service accounts with IRSA annotations
kubectl get sa forge-api-sa -n forge-api -o yaml
kubectl get sa forge-lucy-sa -n forge-api -o yaml
kubectl get sa forge-cost-engine-sa -n forge-workers -o yaml
kubectl get sa prometheus-sa -n forge-system -o yaml
kubectl get sa grafana-sa -n forge-system -o yaml
```

Each service account should have an annotation like:
```yaml
annotations:
  eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/...
```

## Namespace Details

### forge-api

- **Purpose**: Hosts Forge API and Lucy AI service
- **Pod Security**: Restricted (enforces security best practices)
- **Service Accounts**: `forge-api-sa`, `forge-lucy-sa`

### forge-system

- **Purpose**: Hosts monitoring components (Prometheus, Grafana)
- **Pod Security**: Baseline (allows privileged monitoring operations)
- **Service Accounts**: `prometheus-sa`, `grafana-sa`

### forge-workers

- **Purpose**: Hosts Cost Engine and Celery workers
- **Pod Security**: Restricted
- **Service Accounts**: `forge-cost-engine-sa`

## RBAC Details

### forge-api-role

Permissions for Forge API pods:
- Read ConfigMaps (application configuration)
- Read Secrets (managed by External Secrets Operator)
- Read Services (service discovery)
- Read Pods (health checks)

### forge-lucy-role

Same permissions as `forge-api-role` (Lucy runs in same namespace)

### forge-cost-engine-role

Same permissions as `forge-api-role` (for workers namespace)

### prometheus-cluster-role

Cluster-wide permissions for Prometheus:
- Read nodes, services, endpoints, pods (for service discovery)
- Read ConfigMaps (for dynamic configuration)
- Access `/metrics` endpoints (for scraping)

### grafana-role

Namespace-scoped permissions for Grafana:
- Read ConfigMaps and Secrets (for data source configuration)
- Read Services (for service discovery)

## Network Policy Details

### forge-api-network-policy

**Ingress**:
- Allow from ALB/Ingress controller on port 8000
- Allow from same namespace (service-to-service)
- Allow from Prometheus on port 9090 (metrics)

**Egress**:
- Allow DNS (port 53)
- Allow RDS (port 5432)
- Allow Redis (port 6379)
- Allow AWS APIs (port 443)
- Allow same namespace (port 8000)

### forge-workers-network-policy

**Ingress**:
- Allow from Prometheus on port 9090 (metrics)
- Allow from forge-api namespace on port 8000

**Egress**:
- Allow DNS (port 53)
- Allow RDS (port 5432)
- Allow Redis (port 6379)
- Allow AWS APIs (port 443)

### forge-system-network-policy

**Ingress**:
- Allow from ALB to Grafana on port 3000
- Allow Prometheus self-scraping on port 9090

**Egress**:
- Allow DNS (port 53)
- Allow scraping all namespaces (ports 9090, 8000)
- Allow AWS APIs (port 443)
- Allow Grafana to Prometheus (port 9090)

### Default Deny Policies

Each namespace has a default deny ingress policy. This ensures:
- Only explicitly allowed traffic is permitted
- Zero-trust network model
- Defense in depth

## Troubleshooting

### Pods Can't Communicate

Check network policies:
```bash
kubectl describe networkpolicy -n forge-api
```

Test connectivity from a pod:
```bash
kubectl run -it --rm debug --image=nicolaka/netshoot -n forge-api -- /bin/bash
# Inside the pod:
curl http://service-name:8000
```

### Service Account Missing IRSA Annotation

Ensure CDK stacks are deployed:
```bash
aws cloudformation describe-stacks --stack-name ForgeApiStack-dev
```

Re-deploy CDK if needed:
```bash
cd ../
npm run deploy -- -c environment=dev
```

### Permission Denied Errors

Check role bindings:
```bash
kubectl get rolebinding forge-api-rolebinding -n forge-api -o yaml
```

Verify service account is bound to role:
```bash
kubectl auth can-i get configmaps --as=system:serviceaccount:forge-api:forge-api-sa -n forge-api
```

### Network Policy Blocking Traffic

Temporarily disable network policies for debugging:
```bash
kubectl delete networkpolicy forge-api-network-policy -n forge-api
```

Re-apply after debugging:
```bash
kubectl apply -f network-policies.yaml
```

## Security Considerations

### Pod Security Standards

- **Restricted**: Applied to `forge-api` and `forge-workers`
  - Enforces security best practices
  - Prevents privileged containers
  - Requires non-root users
  - Drops all capabilities

- **Baseline**: Applied to `forge-system`
  - Allows monitoring tools that need elevated permissions
  - Still prevents known privilege escalations

### Network Policies

- Default deny all ingress (zero-trust)
- Explicit allow rules for required traffic
- Egress to AWS APIs allowed (for IRSA)
- DNS resolution allowed (required for service discovery)

### RBAC

- Least-privilege principle
- Service accounts have minimal required permissions
- No cluster-admin access
- Namespace-scoped roles where possible

## Next Steps

After applying these manifests:

1. Deploy External Secrets Operator (Task 2.3)
2. Deploy application Helm charts
3. Verify end-to-end connectivity
4. Test IRSA permissions

## References

- [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [EKS IRSA](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)

#!/bin/bash
set -e

# RobCo Forge Kubernetes Manifests Deployment Script
# This script deploys namespaces, RBAC, and network policies to EKS

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if kubectl can connect to cluster
if ! kubectl cluster-info &> /dev/null; then
    print_error "Cannot connect to Kubernetes cluster. Please configure kubectl."
    exit 1
fi

# Get cluster name
CLUSTER_NAME=$(kubectl config current-context)
print_info "Deploying to cluster: $CLUSTER_NAME"

# Confirm deployment
read -p "Do you want to proceed with deployment? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    print_warn "Deployment cancelled."
    exit 0
fi

# Deploy namespaces
print_info "Deploying namespaces..."
kubectl apply -f namespaces.yaml

# Wait for namespaces to be ready
print_info "Waiting for namespaces to be ready..."
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/forge-api --timeout=60s
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/forge-system --timeout=60s
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/forge-workers --timeout=60s

# Deploy RBAC
print_info "Deploying RBAC roles and bindings..."
kubectl apply -f rbac.yaml

# Deploy network policies
print_info "Deploying network policies..."
kubectl apply -f network-policies.yaml

# Verify deployment
print_info "Verifying deployment..."

# Check namespaces
print_info "Checking namespaces..."
kubectl get namespaces | grep forge

# Check roles
print_info "Checking roles..."
kubectl get roles -n forge-api
kubectl get roles -n forge-workers
kubectl get roles -n forge-system

# Check role bindings
print_info "Checking role bindings..."
kubectl get rolebindings -n forge-api
kubectl get rolebindings -n forge-workers
kubectl get rolebindings -n forge-system

# Check cluster roles
print_info "Checking cluster roles..."
kubectl get clusterroles | grep prometheus || print_warn "Prometheus cluster role not found"

# Check network policies
print_info "Checking network policies..."
kubectl get networkpolicies -n forge-api
kubectl get networkpolicies -n forge-workers
kubectl get networkpolicies -n forge-system

# Check service accounts (created by CDK)
print_info "Checking service accounts..."
kubectl get sa -n forge-api | grep forge || print_warn "Service accounts not found in forge-api. Deploy CDK stacks first."
kubectl get sa -n forge-workers | grep forge || print_warn "Service accounts not found in forge-workers. Deploy CDK stacks first."
kubectl get sa -n forge-system | grep -E "prometheus|grafana" || print_warn "Service accounts not found in forge-system. Deploy CDK stacks first."

print_info "Deployment complete!"
print_info ""
print_info "Next steps:"
print_info "1. Deploy CDK stacks to create service accounts with IRSA"
print_info "2. Deploy External Secrets Operator (Task 2.3)"
print_info "3. Deploy application Helm charts"

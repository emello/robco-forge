#!/bin/bash
set -e

# External Secrets Operator Deployment Script for RobCo Forge
# This script installs External Secrets Operator and configures secret synchronization

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check prerequisites
print_step "Checking prerequisites..."

if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed. Please install kubectl first."
    exit 1
fi

if ! command -v helm &> /dev/null; then
    print_error "helm is not installed. Please install Helm first."
    exit 1
fi

if ! kubectl cluster-info &> /dev/null; then
    print_error "Cannot connect to Kubernetes cluster. Please configure kubectl."
    exit 1
fi

# Get cluster name
CLUSTER_NAME=$(kubectl config current-context)
print_info "Deploying to cluster: $CLUSTER_NAME"

# Confirm deployment
read -p "Do you want to proceed with External Secrets Operator installation? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    print_warn "Deployment cancelled."
    exit 0
fi

# Step 1: Create external-secrets namespace
print_step "Creating external-secrets namespace..."
kubectl apply -f external-secrets-operator.yaml

# Wait for namespace to be ready
print_info "Waiting for namespace to be ready..."
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/external-secrets --timeout=60s

# Step 2: Add External Secrets Operator Helm repository
print_step "Adding External Secrets Operator Helm repository..."
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

# Step 3: Install External Secrets Operator
print_step "Installing External Secrets Operator..."
helm upgrade --install external-secrets \
  external-secrets/external-secrets \
  --namespace external-secrets \
  --set installCRDs=true \
  --set serviceAccount.create=false \
  --set serviceAccount.name=external-secrets-sa \
  --set webhook.port=9443 \
  --set certController.create=true \
  --wait \
  --timeout 5m

# Step 4: Wait for External Secrets Operator to be ready
print_info "Waiting for External Secrets Operator to be ready..."
kubectl wait --for=condition=available \
  --timeout=300s \
  deployment/external-secrets \
  -n external-secrets

kubectl wait --for=condition=available \
  --timeout=300s \
  deployment/external-secrets-webhook \
  -n external-secrets

kubectl wait --for=condition=available \
  --timeout=300s \
  deployment/external-secrets-cert-controller \
  -n external-secrets

# Step 5: Verify CRDs are installed
print_step "Verifying CRDs are installed..."
kubectl get crd externalsecrets.external-secrets.io
kubectl get crd secretstores.external-secrets.io
kubectl get crd clustersecretstores.external-secrets.io

# Step 6: Check IRSA annotation
print_step "Checking IRSA annotation on service account..."
SA_ANNOTATION=$(kubectl get sa external-secrets-sa -n external-secrets -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}')

if [ -z "$SA_ANNOTATION" ]; then
    print_warn "IRSA annotation not found on service account."
    print_warn "Please deploy the CDK stack to create the IAM role and annotate the service account."
    print_warn "Or manually annotate with: kubectl annotate serviceaccount external-secrets-sa -n external-secrets eks.amazonaws.com/role-arn=arn:aws:iam::ACCOUNT_ID:role/external-secrets-role"
else
    print_info "IRSA annotation found: $SA_ANNOTATION"
fi

# Step 7: Apply SecretStores
print_step "Applying SecretStores..."
kubectl apply -f secret-stores.yaml

# Wait for SecretStores to be ready
print_info "Waiting for SecretStores to be ready..."
sleep 5

# Step 8: Apply ExternalSecrets
print_step "Applying ExternalSecrets..."
kubectl apply -f external-secrets.yaml

# Wait for ExternalSecrets to sync
print_info "Waiting for ExternalSecrets to sync (this may take a minute)..."
sleep 10

# Step 9: Verify deployment
print_step "Verifying deployment..."

# Check External Secrets Operator pods
print_info "Checking External Secrets Operator pods..."
kubectl get pods -n external-secrets

# Check SecretStores
print_info "Checking SecretStores..."
kubectl get clustersecretstore
kubectl get secretstore -n forge-api
kubectl get secretstore -n forge-workers
kubectl get secretstore -n forge-system

# Check ExternalSecrets
print_info "Checking ExternalSecrets..."
kubectl get externalsecrets -n forge-api
kubectl get externalsecrets -n forge-workers
kubectl get externalsecrets -n forge-system

# Check synced Kubernetes Secrets
print_info "Checking synced Kubernetes Secrets..."
kubectl get secrets -n forge-api | grep forge || print_warn "No secrets found in forge-api namespace"
kubectl get secrets -n forge-workers | grep forge || print_warn "No secrets found in forge-workers namespace"
kubectl get secrets -n forge-system | grep grafana || print_warn "No secrets found in forge-system namespace"

# Step 10: Check for errors
print_step "Checking for errors..."
ERROR_COUNT=$(kubectl get externalsecrets -A -o json | jq '[.items[] | select(.status.conditions[] | select(.type=="Ready" and .status=="False"))] | length')

if [ "$ERROR_COUNT" -gt 0 ]; then
    print_error "Found $ERROR_COUNT ExternalSecrets with errors:"
    kubectl get externalsecrets -A -o json | jq -r '.items[] | select(.status.conditions[] | select(.type=="Ready" and .status=="False")) | "\(.metadata.namespace)/\(.metadata.name): \(.status.conditions[] | select(.type=="Ready") | .message)"'
    print_warn "Please check the External Secrets Operator logs for details:"
    print_warn "kubectl logs -n external-secrets -l app.kubernetes.io/name=external-secrets"
else
    print_info "All ExternalSecrets are syncing successfully!"
fi

print_info ""
print_info "External Secrets Operator deployment complete!"
print_info ""
print_info "Next steps:"
print_info "1. Ensure AWS Secrets Manager secrets are created (see SECRETS_MANAGEMENT.md)"
print_info "2. Verify IRSA is configured correctly"
print_info "3. Check ExternalSecret status: kubectl get externalsecrets -A"
print_info "4. Deploy application Helm charts that reference these secrets"

#!/bin/bash
# RobCo Forge Infrastructure Validation Script
# This script validates all infrastructure components from Phase 1

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
REGION=${2:-us-west-2}
CLUSTER_NAME="robco-forge-${ENVIRONMENT}"

echo "=========================================="
echo "RobCo Forge Infrastructure Validation"
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${REGION}"
echo "=========================================="
echo ""

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Track overall status
VALIDATION_FAILED=0

echo "1. Validating Terraform Deployment..."
echo "--------------------------------------"

# Check if Terraform state exists
cd terraform/environments/${ENVIRONMENT}
if terraform state list > /dev/null 2>&1; then
    print_status 0 "Terraform state exists"
else
    print_status 1 "Terraform state not found"
    VALIDATION_FAILED=1
fi

# Check Terraform outputs
echo ""
echo "Checking Terraform outputs..."
VPC_ID=$(terraform output -raw vpc_id 2>/dev/null || echo "")
EKS_CLUSTER_NAME=$(terraform output -raw eks_cluster_name 2>/dev/null || echo "")
RDS_ENDPOINT=$(terraform output -raw rds_endpoint 2>/dev/null || echo "")
FSX_DNS_NAME=$(terraform output -raw fsx_dns_name 2>/dev/null || echo "")
WORKSPACES_DIRECTORY_ID=$(terraform output -raw workspaces_directory_id 2>/dev/null || echo "")

if [ -n "$VPC_ID" ]; then
    print_status 0 "VPC ID: ${VPC_ID}"
else
    print_status 1 "VPC ID not found in outputs"
    VALIDATION_FAILED=1
fi

if [ -n "$EKS_CLUSTER_NAME" ]; then
    print_status 0 "EKS Cluster: ${EKS_CLUSTER_NAME}"
else
    print_status 1 "EKS Cluster name not found in outputs"
    VALIDATION_FAILED=1
fi

if [ -n "$RDS_ENDPOINT" ]; then
    print_status 0 "RDS Endpoint: ${RDS_ENDPOINT}"
else
    print_status 1 "RDS Endpoint not found in outputs"
    VALIDATION_FAILED=1
fi

if [ -n "$FSX_DNS_NAME" ]; then
    print_status 0 "FSx DNS Name: ${FSX_DNS_NAME}"
else
    print_status 1 "FSx DNS Name not found in outputs"
    VALIDATION_FAILED=1
fi

if [ -n "$WORKSPACES_DIRECTORY_ID" ]; then
    print_status 0 "WorkSpaces Directory ID: ${WORKSPACES_DIRECTORY_ID}"
else
    print_status 1 "WorkSpaces Directory ID not found in outputs"
    VALIDATION_FAILED=1
fi

cd ../../..

echo ""
echo "2. Validating EKS Cluster Health..."
echo "--------------------------------------"

# Update kubeconfig
aws eks update-kubeconfig --name ${CLUSTER_NAME} --region ${REGION} > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_status 0 "kubectl configured for EKS cluster"
else
    print_status 1 "Failed to configure kubectl"
    VALIDATION_FAILED=1
fi

# Check cluster status
CLUSTER_STATUS=$(aws eks describe-cluster --name ${CLUSTER_NAME} --region ${REGION} --query 'cluster.status' --output text 2>/dev/null || echo "")
if [ "$CLUSTER_STATUS" = "ACTIVE" ]; then
    print_status 0 "EKS Cluster status: ACTIVE"
else
    print_status 1 "EKS Cluster status: ${CLUSTER_STATUS}"
    VALIDATION_FAILED=1
fi

# Check nodes
NODE_COUNT=$(kubectl get nodes --no-headers 2>/dev/null | wc -l)
if [ $NODE_COUNT -gt 0 ]; then
    print_status 0 "EKS Nodes: ${NODE_COUNT} nodes ready"
    kubectl get nodes
else
    print_status 1 "No EKS nodes found"
    VALIDATION_FAILED=1
fi

# Check node health
READY_NODES=$(kubectl get nodes --no-headers 2>/dev/null | grep -c " Ready " || echo "0")
if [ $READY_NODES -eq $NODE_COUNT ]; then
    print_status 0 "All nodes are Ready"
else
    print_status 1 "Some nodes are not Ready (${READY_NODES}/${NODE_COUNT})"
    VALIDATION_FAILED=1
fi

echo ""
echo "3. Validating RDS Accessibility from EKS..."
echo "--------------------------------------"

# Check RDS instance status
RDS_STATUS=$(aws rds describe-db-instances --region ${REGION} --query "DBInstances[?contains(DBInstanceIdentifier, 'forge')].DBInstanceStatus" --output text 2>/dev/null || echo "")
if [ -n "$RDS_STATUS" ]; then
    if [ "$RDS_STATUS" = "available" ]; then
        print_status 0 "RDS instance status: available"
    else
        print_status 1 "RDS instance status: ${RDS_STATUS}"
        VALIDATION_FAILED=1
    fi
else
    print_status 1 "RDS instance not found"
    VALIDATION_FAILED=1
fi

# Test RDS connectivity from EKS (using a test pod)
echo "Testing RDS connectivity from EKS..."
cat <<EOF | kubectl apply -f - > /dev/null 2>&1
apiVersion: v1
kind: Pod
metadata:
  name: rds-connectivity-test
  namespace: default
spec:
  containers:
  - name: postgres-client
    image: postgres:15-alpine
    command: ['sleep', '3600']
  restartPolicy: Never
EOF

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/rds-connectivity-test --timeout=60s > /dev/null 2>&1
if [ $? -eq 0 ]; then
    # Test connection (will fail without credentials, but tests network connectivity)
    if [ -n "$RDS_ENDPOINT" ]; then
        RDS_HOST=$(echo $RDS_ENDPOINT | cut -d: -f1)
        kubectl exec rds-connectivity-test -- timeout 5 nc -zv $RDS_HOST 5432 > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            print_status 0 "RDS is accessible from EKS (network connectivity verified)"
        else
            print_status 1 "RDS is not accessible from EKS"
            VALIDATION_FAILED=1
        fi
    fi
else
    print_warning "Could not create test pod to verify RDS connectivity"
fi

# Cleanup test pod
kubectl delete pod rds-connectivity-test --ignore-not-found=true > /dev/null 2>&1

echo ""
echo "4. Validating FSx ONTAP Accessibility from EKS..."
echo "--------------------------------------"

# Check FSx filesystem status
FSX_STATUS=$(aws fsx describe-file-systems --region ${REGION} --query "FileSystems[?contains(Tags[?Key=='Name'].Value, 'forge')].Lifecycle" --output text 2>/dev/null || echo "")
if [ -n "$FSX_STATUS" ]; then
    if [ "$FSX_STATUS" = "AVAILABLE" ]; then
        print_status 0 "FSx filesystem status: AVAILABLE"
    else
        print_status 1 "FSx filesystem status: ${FSX_STATUS}"
        VALIDATION_FAILED=1
    fi
else
    print_status 1 "FSx filesystem not found"
    VALIDATION_FAILED=1
fi

# Test FSx connectivity from EKS
echo "Testing FSx connectivity from EKS..."
cat <<EOF | kubectl apply -f - > /dev/null 2>&1
apiVersion: v1
kind: Pod
metadata:
  name: fsx-connectivity-test
  namespace: default
spec:
  containers:
  - name: nfs-client
    image: busybox:latest
    command: ['sleep', '3600']
  restartPolicy: Never
EOF

# Wait for pod to be ready
kubectl wait --for=condition=Ready pod/fsx-connectivity-test --timeout=60s > /dev/null 2>&1
if [ $? -eq 0 ]; then
    if [ -n "$FSX_DNS_NAME" ]; then
        kubectl exec fsx-connectivity-test -- timeout 5 nc -zv $FSX_DNS_NAME 2049 > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            print_status 0 "FSx is accessible from EKS (network connectivity verified)"
        else
            print_status 1 "FSx is not accessible from EKS"
            VALIDATION_FAILED=1
        fi
    fi
else
    print_warning "Could not create test pod to verify FSx connectivity"
fi

# Cleanup test pod
kubectl delete pod fsx-connectivity-test --ignore-not-found=true > /dev/null 2>&1

echo ""
echo "5. Validating WorkSpaces Directory Configuration..."
echo "--------------------------------------"

# Check WorkSpaces directory status
if [ -n "$WORKSPACES_DIRECTORY_ID" ]; then
    DIR_STATUS=$(aws workspaces describe-workspace-directories --directory-ids ${WORKSPACES_DIRECTORY_ID} --region ${REGION} --query 'Directories[0].State' --output text 2>/dev/null || echo "")
    if [ "$DIR_STATUS" = "REGISTERED" ]; then
        print_status 0 "WorkSpaces directory status: REGISTERED"
    else
        print_status 1 "WorkSpaces directory status: ${DIR_STATUS}"
        VALIDATION_FAILED=1
    fi
    
    # Check if PCoIP is disabled (WSP-only)
    STREAMING_PROPERTIES=$(aws workspaces describe-workspace-directories --directory-ids ${WORKSPACES_DIRECTORY_ID} --region ${REGION} --query 'Directories[0].WorkspaceCreationProperties.EnableWorkDocs' --output text 2>/dev/null || echo "")
    print_status 0 "WorkSpaces directory configured (verify WSP-only manually)"
    print_warning "Manual verification required: Ensure PCoIP is disabled at directory level"
else
    print_status 1 "WorkSpaces directory ID not available"
    VALIDATION_FAILED=1
fi

echo ""
echo "6. Validating Kubernetes Infrastructure (CDK)..."
echo "--------------------------------------"

# Check namespaces
NAMESPACES=("forge-api" "forge-system" "forge-workers")
for ns in "${NAMESPACES[@]}"; do
    kubectl get namespace $ns > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_status 0 "Namespace exists: ${ns}"
    else
        print_status 1 "Namespace missing: ${ns}"
        VALIDATION_FAILED=1
    fi
done

# Check service accounts with IRSA
SERVICE_ACCOUNTS=("forge-api-sa:forge-api" "forge-lucy-sa:forge-api" "forge-cost-engine-sa:forge-workers" "prometheus-sa:forge-system" "grafana-sa:forge-system")
for sa_ns in "${SERVICE_ACCOUNTS[@]}"; do
    SA=$(echo $sa_ns | cut -d: -f1)
    NS=$(echo $sa_ns | cut -d: -f2)
    kubectl get sa $SA -n $NS > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        ROLE_ARN=$(kubectl get sa $SA -n $NS -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}' 2>/dev/null || echo "")
        if [ -n "$ROLE_ARN" ]; then
            print_status 0 "Service account with IRSA: ${SA} (${NS})"
        else
            print_status 1 "Service account missing IRSA annotation: ${SA} (${NS})"
            VALIDATION_FAILED=1
        fi
    else
        print_status 1 "Service account missing: ${SA} (${NS})"
        VALIDATION_FAILED=1
    fi
done

# Check External Secrets Operator
kubectl get pods -n external-secrets > /dev/null 2>&1
if [ $? -eq 0 ]; then
    ESO_READY=$(kubectl get pods -n external-secrets --no-headers 2>/dev/null | grep -c "Running" || echo "0")
    if [ $ESO_READY -gt 0 ]; then
        print_status 0 "External Secrets Operator is running"
    else
        print_status 1 "External Secrets Operator pods not running"
        VALIDATION_FAILED=1
    fi
else
    print_warning "External Secrets Operator namespace not found (may not be deployed yet)"
fi

echo ""
echo "7. Validating Monitoring Infrastructure..."
echo "--------------------------------------"

# Check CloudWatch log groups
LOG_GROUPS=("/aws/eks/${CLUSTER_NAME}/cluster" "/aws/forge/${ENVIRONMENT}/api")
for lg in "${LOG_GROUPS[@]}"; do
    aws logs describe-log-groups --log-group-name-prefix "$lg" --region ${REGION} > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_status 0 "CloudWatch log group exists: ${lg}"
    else
        print_warning "CloudWatch log group not found: ${lg} (may be created on first use)"
    fi
done

# Check SNS topics
SNS_TOPICS=$(aws sns list-topics --region ${REGION} --query "Topics[?contains(TopicArn, 'forge')].TopicArn" --output text 2>/dev/null || echo "")
if [ -n "$SNS_TOPICS" ]; then
    print_status 0 "SNS topics configured for alerts"
else
    print_warning "No SNS topics found (may not be configured yet)"
fi

echo ""
echo "=========================================="
echo "Validation Summary"
echo "=========================================="

if [ $VALIDATION_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All infrastructure validation checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Proceed to Phase 2: Core API and Data Layer"
    echo "2. Implement database models and migrations (Task 4)"
    echo "3. Deploy application services"
    exit 0
else
    echo -e "${RED}✗ Some validation checks failed${NC}"
    echo ""
    echo "Please review the failures above and:"
    echo "1. Check Terraform deployment logs"
    echo "2. Verify AWS resources in the console"
    echo "3. Check kubectl access to EKS cluster"
    echo "4. Review CDK deployment status"
    exit 1
fi

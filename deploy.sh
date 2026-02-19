#!/bin/bash

# RobCo Forge - Deployment Script
# This script automates the deployment process for RobCo Forge platform

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
VERSION=${2:-v1.0.0}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RobCo Forge Deployment Script${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}Version: ${VERSION}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Terraform
    if command -v terraform &> /dev/null; then
        TERRAFORM_VERSION=$(terraform version -json | grep -o '"terraform_version":"[^"]*' | cut -d'"' -f4)
        print_status "Terraform installed: $TERRAFORM_VERSION"
    else
        print_error "Terraform not found. Please install Terraform >= 1.5.0"
        exit 1
    fi
    
    # Check AWS CLI
    if command -v aws &> /dev/null; then
        AWS_VERSION=$(aws --version | cut -d' ' -f1 | cut -d'/' -f2)
        print_status "AWS CLI installed: $AWS_VERSION"
    else
        print_error "AWS CLI not found. Please install AWS CLI >= 2.0"
        exit 1
    fi
    
    # Check kubectl
    if command -v kubectl &> /dev/null; then
        KUBECTL_VERSION=$(kubectl version --client -o json | grep -o '"gitVersion":"[^"]*' | cut -d'"' -f4)
        print_status "kubectl installed: $KUBECTL_VERSION"
    else
        print_error "kubectl not found. Please install kubectl >= 1.27"
        exit 1
    fi
    
    # Check Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_status "Node.js installed: $NODE_VERSION"
    else
        print_error "Node.js not found. Please install Node.js >= 18.0"
        exit 1
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_status "Python installed: $PYTHON_VERSION"
    else
        print_error "Python not found. Please install Python >= 3.11"
        exit 1
    fi
    
    # Check Docker
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
        print_status "Docker installed: $DOCKER_VERSION"
    else
        print_error "Docker not found. Please install Docker >= 24.0"
        exit 1
    fi
    
    echo ""
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_info "Deploying infrastructure with Terraform..."
    
    cd terraform/environments/${ENVIRONMENT}
    
    # Initialize Terraform
    print_info "Initializing Terraform..."
    terraform init
    
    # Plan
    print_info "Creating Terraform plan..."
    terraform plan -out=tfplan
    
    # Ask for confirmation
    echo ""
    read -p "Review the plan above. Continue with apply? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        print_warning "Deployment cancelled by user"
        exit 0
    fi
    
    # Apply
    print_info "Applying Terraform configuration..."
    terraform apply tfplan
    
    print_status "Infrastructure deployment complete"
    
    # Capture outputs
    print_info "Capturing Terraform outputs..."
    EKS_CLUSTER=$(terraform output -raw eks_cluster_name)
    RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
    FSX_FILESYSTEM_ID=$(terraform output -raw fsx_filesystem_id)
    
    print_status "EKS Cluster: $EKS_CLUSTER"
    print_status "RDS Endpoint: $RDS_ENDPOINT"
    print_status "FSx Filesystem: $FSX_FILESYSTEM_ID"
    
    cd ../../..
    echo ""
}

# Function to deploy Kubernetes resources
deploy_kubernetes() {
    print_info "Deploying Kubernetes resources with CDK..."
    
    cd cdk
    
    # Install dependencies
    print_info "Installing CDK dependencies..."
    npm install
    
    # Deploy CDK stacks
    print_info "Deploying CDK stacks..."
    cdk deploy --all --require-approval never
    
    print_status "Kubernetes resources deployed"
    
    cd ..
    echo ""
}

# Function to configure secrets
configure_secrets() {
    print_info "Configuring secrets in AWS Secrets Manager..."
    
    print_warning "You need to manually update the secret values after creation"
    
    # Database secret
    aws secretsmanager create-secret \
        --name forge/${ENVIRONMENT}/database \
        --secret-string '{"username":"forge","password":"CHANGE_ME"}' \
        2>/dev/null || print_warning "Database secret already exists"
    
    # Anthropic secret
    aws secretsmanager create-secret \
        --name forge/${ENVIRONMENT}/anthropic \
        --secret-string '{"api_key":"CHANGE_ME"}' \
        2>/dev/null || print_warning "Anthropic secret already exists"
    
    # Okta secret
    aws secretsmanager create-secret \
        --name forge/${ENVIRONMENT}/okta \
        --secret-string '{"client_id":"CHANGE_ME","client_secret":"CHANGE_ME","domain":"CHANGE_ME"}' \
        2>/dev/null || print_warning "Okta secret already exists"
    
    # JWT secret
    aws secretsmanager create-secret \
        --name forge/${ENVIRONMENT}/jwt \
        --secret-string '{"secret":"CHANGE_ME"}' \
        2>/dev/null || print_warning "JWT secret already exists"
    
    print_status "Secrets configured (remember to update values)"
    echo ""
}

# Function to setup database
setup_database() {
    print_info "Setting up database..."
    
    cd api
    
    # Install dependencies
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Run migrations
    print_info "Running database migrations..."
    print_warning "Make sure DATABASE_URL environment variable is set"
    
    if [ -z "$DATABASE_URL" ]; then
        print_error "DATABASE_URL not set. Please set it and run migrations manually:"
        print_info "  export DATABASE_URL='postgresql://forge:PASSWORD@RDS_ENDPOINT:5432/forge'"
        print_info "  alembic upgrade head"
    else
        alembic upgrade head
        print_status "Database migrations complete"
    fi
    
    cd ..
    echo ""
}

# Function to build and deploy API
deploy_api() {
    print_info "Building and deploying API services..."
    
    cd api
    
    # Build Docker image
    print_info "Building Docker image..."
    docker build -t forge-api:${VERSION} .
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=$(aws configure get region)
    
    # Login to ECR
    print_info "Logging in to ECR..."
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
    
    # Tag and push
    print_info "Pushing image to ECR..."
    docker tag forge-api:${VERSION} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/forge-api:${VERSION}
    docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/forge-api:${VERSION}
    
    print_status "API image pushed to ECR"
    
    # Deploy to Kubernetes
    print_info "Deploying to Kubernetes..."
    kubectl apply -f k8s/api-deployment.yaml
    kubectl apply -f k8s/api-service.yaml
    kubectl apply -f k8s/api-ingress.yaml
    
    # Wait for rollout
    print_info "Waiting for rollout to complete..."
    kubectl rollout status deployment/forge-api -n forge-api
    
    print_status "API deployment complete"
    
    cd ..
    echo ""
}

# Function to build and deploy CLI
deploy_cli() {
    print_info "Building CLI..."
    
    cd cli
    
    # Install dependencies
    print_info "Installing dependencies..."
    npm install
    
    # Build
    print_info "Building CLI..."
    npm run build
    
    # Package
    print_info "Packaging CLI..."
    npm pack
    
    print_status "CLI built: forge-cli-1.0.0.tgz"
    print_info "To install: npm install -g ./forge-cli-1.0.0.tgz"
    
    cd ..
    echo ""
}

# Function to build and deploy Portal
deploy_portal() {
    print_info "Building and deploying Portal..."
    
    cd portal
    
    # Install dependencies
    print_info "Installing dependencies..."
    npm install
    
    # Set environment variables
    print_info "Configuring environment..."
    cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://api.forge.${ENVIRONMENT}.example.com
NEXT_PUBLIC_WS_URL=wss://api.forge.${ENVIRONMENT}.example.com/ws
EOF
    
    # Build
    print_info "Building Portal..."
    npm run build
    
    print_status "Portal built successfully"
    print_info "Deploy options:"
    print_info "  1. Vercel: vercel --prod"
    print_info "  2. Docker: docker build -t forge-portal:${VERSION} ."
    print_info "  3. Static: npm run export && aws s3 sync out/ s3://bucket/"
    
    cd ..
    echo ""
}

# Function to run smoke tests
run_smoke_tests() {
    print_info "Running smoke tests..."
    
    # Get API URL
    API_URL="https://api.forge.${ENVIRONMENT}.example.com"
    
    # Test health endpoint
    print_info "Testing health endpoint..."
    if curl -f -s ${API_URL}/health > /dev/null; then
        print_status "Health check passed"
    else
        print_error "Health check failed"
    fi
    
    # Test OpenAPI docs
    print_info "Testing OpenAPI docs..."
    if curl -f -s ${API_URL}/docs > /dev/null; then
        print_status "OpenAPI docs accessible"
    else
        print_error "OpenAPI docs not accessible"
    fi
    
    echo ""
}

# Main deployment flow
main() {
    check_prerequisites
    
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Starting deployment to ${ENVIRONMENT}${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    
    # Ask what to deploy
    echo "What would you like to deploy?"
    echo "1. Full deployment (infrastructure + services)"
    echo "2. Infrastructure only"
    echo "3. Services only (API + CLI + Portal)"
    echo "4. API only"
    echo "5. Portal only"
    echo "6. CLI only"
    echo ""
    read -p "Enter choice (1-6): " CHOICE
    
    case $CHOICE in
        1)
            deploy_infrastructure
            deploy_kubernetes
            configure_secrets
            setup_database
            deploy_api
            deploy_cli
            deploy_portal
            run_smoke_tests
            ;;
        2)
            deploy_infrastructure
            deploy_kubernetes
            configure_secrets
            ;;
        3)
            setup_database
            deploy_api
            deploy_cli
            deploy_portal
            run_smoke_tests
            ;;
        4)
            deploy_api
            run_smoke_tests
            ;;
        5)
            deploy_portal
            ;;
        6)
            deploy_cli
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    print_info "Next steps:"
    print_info "1. Update secrets in AWS Secrets Manager"
    print_info "2. Run full smoke tests (see DEPLOYMENT_CHECKLIST.md)"
    print_info "3. Monitor logs and metrics"
    print_info "4. Onboard users"
    echo ""
}

# Run main function
main

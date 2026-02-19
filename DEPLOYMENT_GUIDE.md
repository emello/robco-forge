# RobCo Forge - Deployment Guide

## Overview
This guide provides instructions for deploying the complete RobCo Forge platform to production.

## Architecture Overview

The RobCo Forge platform consists of:
1. **Infrastructure** (Terraform + AWS CDK) - AWS resources, networking, Kubernetes
2. **API Services** (Python/FastAPI) - Core API, authentication, RBAC
3. **Provisioning Service** (Python) - WorkSpace lifecycle management
4. **Lucy AI Service** (Python) - Anthropic Claude integration
5. **Cost Engine** (Python) - Cost tracking and optimization
6. **CLI** (TypeScript/Node.js) - Command-line interface
7. **Portal** (Next.js/React) - Web interface

## Prerequisites

### Required Tools
- Terraform >= 1.5.0
- AWS CLI >= 2.0
- kubectl >= 1.27
- Node.js >= 18.0
- Python >= 3.11
- Docker >= 24.0

### AWS Account Setup
- AWS account with appropriate permissions
- IAM roles configured for EKS, RDS, FSx, WorkSpaces
- VPC and networking configured
- Domain name for portal (optional)

### External Services
- Okta account for SSO
- Anthropic API key for Claude (or AWS Bedrock access)
- SMTP server for email notifications (optional)
- Slack workspace for notifications (optional)

## Phase 1: Infrastructure Deployment

### 1.1 Deploy Terraform Infrastructure

```bash
cd terraform/environments/production

# Initialize Terraform
terraform init

# Review plan
terraform plan -out=tfplan

# Apply infrastructure
terraform apply tfplan
```

This creates:
- VPCs and networking
- EKS cluster
- RDS PostgreSQL database
- FSx ONTAP filesystem
- WorkSpaces directory
- CloudWatch log groups
- Prometheus and Grafana

### 1.2 Deploy Kubernetes Resources

```bash
cd cdk

# Install dependencies
npm install

# Deploy CDK stacks
cdk deploy --all --require-approval never
```

This creates:
- Kubernetes namespaces
- RBAC roles and bindings
- Network policies
- External Secrets Operator
- Service accounts with IRSA

### 1.3 Configure Secrets

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name forge/database \
  --secret-string '{"username":"forge","password":"<password>"}'

aws secretsmanager create-secret \
  --name forge/anthropic \
  --secret-string '{"api_key":"<anthropic-api-key>"}'

aws secretsmanager create-secret \
  --name forge/okta \
  --secret-string '{"client_id":"<okta-client-id>","client_secret":"<okta-client-secret>"}'
```

## Phase 2: Database Setup

### 2.1 Run Database Migrations

```bash
cd api

# Install dependencies
pip install -r requirements.txt

# Set database URL
export DATABASE_URL="postgresql://forge:<password>@<rds-endpoint>:5432/forge"

# Run migrations
alembic upgrade head
```

### 2.2 Create Initial Data

```bash
# Create admin user
python scripts/create_admin_user.py

# Create default blueprints
python scripts/create_default_blueprints.py
```

## Phase 3: API Services Deployment

### 3.1 Build Docker Images

```bash
cd api

# Build API image
docker build -t forge-api:latest .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag forge-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/forge-api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/forge-api:latest
```

### 3.2 Deploy to Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
kubectl apply -f k8s/api-ingress.yaml

# Verify deployment
kubectl get pods -n forge-api
kubectl logs -n forge-api -l app=forge-api
```

### 3.3 Configure Load Balancer

```bash
# Get load balancer URL
kubectl get ingress -n forge-api

# Configure DNS
# Point api.forge.example.com to load balancer
```

## Phase 4: CLI Deployment

### 4.1 Build CLI

```bash
cd cli

# Install dependencies
npm install

# Build
npm run build

# Package
npm pack
```

### 4.2 Publish CLI

```bash
# Publish to npm (if public)
npm publish

# Or distribute binary
npm run package
```

### 4.3 Install CLI

```bash
# Install globally
npm install -g @robco/forge-cli

# Configure
forge config set api-url https://api.forge.example.com
forge config set auth-method okta
```

## Phase 5: Portal Deployment

### 5.1 Build Portal

```bash
cd portal

# Install dependencies
npm install

# Set environment variables
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://api.forge.example.com
NEXT_PUBLIC_WS_URL=wss://api.forge.example.com/ws
EOF

# Build
npm run build
```

### 5.2 Deploy Portal

#### Option A: Vercel (Recommended)
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

#### Option B: Docker
```bash
# Build Docker image
docker build -t forge-portal:latest .

# Push to ECR
docker tag forge-portal:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/forge-portal:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/forge-portal:latest

# Deploy to Kubernetes
kubectl apply -f k8s/portal-deployment.yaml
```

#### Option C: Static Export
```bash
# Build static export
npm run build
npm run export

# Deploy to S3 + CloudFront
aws s3 sync out/ s3://forge-portal-bucket/
aws cloudfront create-invalidation --distribution-id <dist-id> --paths "/*"
```

### 5.3 Configure DNS

```bash
# Point portal.forge.example.com to deployment
# Vercel: Use Vercel DNS or CNAME
# Kubernetes: Use load balancer URL
# S3: Use CloudFront distribution
```

## Phase 6: Monitoring Setup

### 6.1 Configure Prometheus

```bash
# Verify Prometheus is running
kubectl get pods -n forge-system -l app=prometheus

# Access Prometheus UI
kubectl port-forward -n forge-system svc/prometheus 9090:9090
```

### 6.2 Configure Grafana

```bash
# Get Grafana admin password
kubectl get secret -n forge-system grafana-admin -o jsonpath='{.data.password}' | base64 -d

# Access Grafana UI
kubectl port-forward -n forge-system svc/grafana 3000:3000

# Import dashboards from grafana/dashboards/
```

### 6.3 Configure CloudWatch Alarms

```bash
# Create alarms for critical metrics
aws cloudwatch put-metric-alarm \
  --alarm-name forge-api-high-error-rate \
  --alarm-description "Alert when API error rate exceeds 5%" \
  --metric-name ErrorRate \
  --namespace Forge/API \
  --statistic Average \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

## Phase 7: Validation

### 7.1 Smoke Tests

```bash
# Test API health
curl https://api.forge.example.com/health

# Test authentication
forge login

# Test workspace provisioning
forge launch --bundle STANDARD --os Windows

# Test portal
open https://portal.forge.example.com
```

### 7.2 End-to-End Tests

```bash
cd api
pytest tests/e2e/

cd portal
npm run test:e2e
```

### 7.3 Load Testing

```bash
# Run load tests
cd api
locust -f tests/load/locustfile.py --host https://api.forge.example.com
```

## Phase 8: Post-Deployment

### 8.1 Monitor Logs

```bash
# API logs
kubectl logs -n forge-api -l app=forge-api --tail=100 -f

# Portal logs (if on Kubernetes)
kubectl logs -n forge-portal -l app=forge-portal --tail=100 -f

# CloudWatch logs
aws logs tail /aws/eks/forge/cluster --follow
```

### 8.2 Monitor Metrics

- Check Grafana dashboards
- Review CloudWatch metrics
- Monitor cost tracking accuracy
- Verify budget enforcement

### 8.3 User Onboarding

```bash
# Create user accounts
python scripts/create_users.py --csv users.csv

# Assign roles
python scripts/assign_roles.py --user alice@example.com --role team_lead

# Set budgets
python scripts/set_budgets.py --team engineering --amount 5000
```

## Rollback Procedures

### API Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/forge-api -n forge-api

# Verify rollback
kubectl rollout status deployment/forge-api -n forge-api
```

### Portal Rollback

```bash
# Vercel
vercel rollback

# Kubernetes
kubectl rollout undo deployment/forge-portal -n forge-portal
```

### Database Rollback

```bash
# Rollback migration
cd api
alembic downgrade -1
```

## Troubleshooting

### API Not Responding

```bash
# Check pod status
kubectl get pods -n forge-api

# Check logs
kubectl logs -n forge-api -l app=forge-api

# Check database connectivity
kubectl exec -it -n forge-api <pod-name> -- python -c "from src.database import engine; engine.connect()"
```

### Portal Not Loading

```bash
# Check build logs
npm run build

# Check environment variables
cat .env.production

# Check API connectivity
curl https://api.forge.example.com/health
```

### WorkSpace Provisioning Failing

```bash
# Check AWS WorkSpaces service status
aws workspaces describe-workspaces

# Check IAM permissions
aws iam get-role --role-name ForgeWorkSpacesRole

# Check logs
kubectl logs -n forge-api -l app=forge-api | grep "workspace"
```

## Security Checklist

- [ ] All secrets stored in AWS Secrets Manager
- [ ] TLS/SSL certificates configured
- [ ] Network policies enforced
- [ ] RBAC roles configured correctly
- [ ] Security groups restrict access
- [ ] Audit logging enabled
- [ ] Encryption at rest enabled (RDS, FSx, EBS)
- [ ] Encryption in transit enabled (TLS 1.3)
- [ ] MFA enabled for admin accounts
- [ ] Regular security scans scheduled

## Maintenance

### Daily
- Monitor CloudWatch alarms
- Review error logs
- Check cost tracking accuracy

### Weekly
- Review Grafana dashboards
- Check for failed WorkSpace provisions
- Review budget utilization

### Monthly
- Update dependencies
- Review security patches
- Optimize costs based on recommendations
- Review and update budgets

### Quarterly
- Disaster recovery drill
- Security audit
- Performance optimization
- User feedback review

## Support

### Documentation
- API Documentation: https://api.forge.example.com/docs
- Portal Documentation: https://portal.forge.example.com/docs
- CLI Documentation: `forge --help`

### Contact
- Technical Support: support@robco.com
- Security Issues: security@robco.com
- Feature Requests: GitHub Issues

## Appendix

### Environment Variables

#### API Service
```env
DATABASE_URL=postgresql://forge:<password>@<rds-endpoint>:5432/forge
REDIS_URL=redis://<redis-endpoint>:6379
ANTHROPIC_API_KEY=<api-key>
OKTA_CLIENT_ID=<client-id>
OKTA_CLIENT_SECRET=<client-secret>
OKTA_DOMAIN=<okta-domain>
AWS_REGION=us-east-1
LOG_LEVEL=INFO
```

#### Portal
```env
NEXT_PUBLIC_API_URL=https://api.forge.example.com
NEXT_PUBLIC_WS_URL=wss://api.forge.example.com/ws
```

#### CLI
```env
FORGE_API_URL=https://api.forge.example.com
FORGE_AUTH_METHOD=okta
```

### Resource Requirements

#### API Service
- CPU: 2 vCPU per pod
- Memory: 4 GB per pod
- Replicas: 3 minimum (auto-scale to 10)

#### Portal
- CPU: 1 vCPU per pod
- Memory: 2 GB per pod
- Replicas: 2 minimum (auto-scale to 5)

#### Database
- Instance: db.r6g.xlarge (4 vCPU, 32 GB RAM)
- Storage: 500 GB SSD
- Multi-AZ: Yes

#### FSx ONTAP
- Storage: 1 TB
- Throughput: 256 MB/s
- Multi-AZ: Yes

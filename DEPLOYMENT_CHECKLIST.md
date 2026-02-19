# RobCo Forge - Deployment Checklist

## Pre-Deployment Verification

### Code Quality Checks
- [ ] All TypeScript files compile without errors
- [ ] All Python files pass type checking (mypy)
- [ ] No critical linting errors
- [ ] All required environment variables documented

### Testing Status
- [ ] Unit tests pass for API services
- [ ] Integration tests pass for critical flows
- [ ] Lucy conversation corpus tests pass
- [ ] Portal builds successfully

### Documentation Review
- [ ] API documentation complete (OpenAPI/Swagger)
- [ ] User guides available (Portal, CLI, Lucy)
- [ ] Deployment guide reviewed
- [ ] Architecture documentation current

## Environment Setup

### AWS Account Prerequisites
- [ ] AWS account with appropriate permissions
- [ ] IAM roles created for EKS, RDS, FSx, WorkSpaces
- [ ] AWS CLI configured with credentials
- [ ] Terraform state backend configured (S3 + DynamoDB)

### External Services
- [ ] Okta SSO configured
  - [ ] SAML 2.0 application created
  - [ ] Client ID and secret obtained
  - [ ] Callback URLs configured
- [ ] Anthropic API access
  - [ ] API key obtained (or AWS Bedrock access configured)
  - [ ] Rate limits understood
- [ ] Domain names registered (optional)
  - [ ] api.forge.example.com
  - [ ] portal.forge.example.com

### Development Tools
- [ ] Terraform >= 1.5.0 installed
- [ ] AWS CLI >= 2.0 installed
- [ ] kubectl >= 1.27 installed
- [ ] Node.js >= 18.0 installed
- [ ] Python >= 3.11 installed
- [ ] Docker >= 24.0 installed

## Phase 1: Infrastructure Deployment (Staging)

### 1.1 Terraform Infrastructure
```bash
cd terraform/environments/staging
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

**Verify:**
- [ ] VPCs created with correct CIDR blocks
- [ ] EKS cluster healthy and accessible
- [ ] RDS PostgreSQL instance running (Multi-AZ)
- [ ] FSx ONTAP filesystem available
- [ ] WorkSpaces directory configured
- [ ] CloudWatch log groups created
- [ ] Prometheus and Grafana deployed

**Capture Outputs:**
- [ ] EKS cluster endpoint: _______________
- [ ] RDS endpoint: _______________
- [ ] FSx filesystem ID: _______________
- [ ] WorkSpaces directory ID: _______________

### 1.2 Kubernetes Resources (CDK)
```bash
cd cdk
npm install
cdk deploy --all --require-approval never
```

**Verify:**
- [ ] Namespaces created (forge-api, forge-system, forge-workers)
- [ ] RBAC roles and bindings configured
- [ ] Network policies applied
- [ ] External Secrets Operator running
- [ ] Service accounts with IRSA created

### 1.3 Secrets Configuration
```bash
# Database credentials
aws secretsmanager create-secret \
  --name forge/staging/database \
  --secret-string '{"username":"forge","password":"CHANGE_ME"}'

# Anthropic API key
aws secretsmanager create-secret \
  --name forge/staging/anthropic \
  --secret-string '{"api_key":"CHANGE_ME"}'

# Okta SSO credentials
aws secretsmanager create-secret \
  --name forge/staging/okta \
  --secret-string '{"client_id":"CHANGE_ME","client_secret":"CHANGE_ME","domain":"CHANGE_ME"}'

# JWT secret
aws secretsmanager create-secret \
  --name forge/staging/jwt \
  --secret-string '{"secret":"CHANGE_ME"}'
```

**Verify:**
- [ ] All secrets created in AWS Secrets Manager
- [ ] External Secrets Operator syncing secrets to Kubernetes
- [ ] Secrets available in appropriate namespaces

## Phase 2: Database Setup

### 2.1 Database Migrations
```bash
cd api
pip install -r requirements.txt

export DATABASE_URL="postgresql://forge:PASSWORD@RDS_ENDPOINT:5432/forge"
alembic upgrade head
```

**Verify:**
- [ ] All migrations applied successfully
- [ ] Tables created: workspaces, blueprints, cost_records, user_budgets, audit_logs, users
- [ ] Indexes created
- [ ] Partitioning configured for audit_logs

### 2.2 Initial Data
```bash
# Create admin user
python scripts/create_admin_user.py

# Create default blueprints
python scripts/create_default_blueprints.py
```

**Verify:**
- [ ] Admin user created
- [ ] Default blueprints available
- [ ] Can query database successfully

## Phase 3: API Services Deployment

### 3.1 Build and Push Docker Images
```bash
cd api

# Build image
docker build -t forge-api:v1.0.0 .

# Tag and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
docker tag forge-api:v1.0.0 ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/forge-api:v1.0.0
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/forge-api:v1.0.0
```

**Verify:**
- [ ] Docker image builds successfully
- [ ] Image pushed to ECR
- [ ] Image size reasonable (< 1GB)

### 3.2 Deploy to Kubernetes
```bash
# Update image tag in manifests
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
kubectl apply -f k8s/api-ingress.yaml

# Wait for rollout
kubectl rollout status deployment/forge-api -n forge-api
```

**Verify:**
- [ ] Pods running (3 replicas)
- [ ] No crash loops
- [ ] Health checks passing
- [ ] Logs show successful startup

### 3.3 Test API Endpoints
```bash
# Get load balancer URL
kubectl get ingress -n forge-api

# Test health endpoint
curl https://api.forge.staging.example.com/health

# Test OpenAPI docs
curl https://api.forge.staging.example.com/docs
```

**Verify:**
- [ ] Health endpoint returns 200
- [ ] OpenAPI documentation accessible
- [ ] Authentication endpoint responds

## Phase 4: CLI Deployment

### 4.1 Build CLI
```bash
cd cli
npm install
npm run build
npm pack
```

**Verify:**
- [ ] TypeScript compiles successfully
- [ ] Package created (forge-cli-1.0.0.tgz)

### 4.2 Test CLI Locally
```bash
npm install -g ./forge-cli-1.0.0.tgz

forge config set api-url https://api.forge.staging.example.com
forge config set auth-method okta

# Test login
forge login

# Test workspace list
forge list
```

**Verify:**
- [ ] CLI installs successfully
- [ ] Configuration persists
- [ ] Authentication works
- [ ] Commands execute without errors

## Phase 5: Portal Deployment

### 5.1 Build Portal
```bash
cd portal
npm install

# Set environment variables
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://api.forge.staging.example.com
NEXT_PUBLIC_WS_URL=wss://api.forge.staging.example.com/ws
EOF

npm run build
```

**Verify:**
- [ ] Build completes successfully
- [ ] No TypeScript errors
- [ ] Static files generated in .next directory

### 5.2 Deploy Portal (Choose One)

#### Option A: Vercel (Recommended)
```bash
npm install -g vercel
vercel --prod
```

#### Option B: Docker + Kubernetes
```bash
docker build -t forge-portal:v1.0.0 .
docker tag forge-portal:v1.0.0 ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/forge-portal:v1.0.0
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/forge-portal:v1.0.0

kubectl apply -f k8s/portal-deployment.yaml
kubectl apply -f k8s/portal-service.yaml
kubectl apply -f k8s/portal-ingress.yaml
```

#### Option C: Static Export to S3 + CloudFront
```bash
npm run build
npm run export

aws s3 sync out/ s3://forge-portal-staging/
aws cloudfront create-invalidation --distribution-id DIST_ID --paths "/*"
```

**Verify:**
- [ ] Portal accessible at URL
- [ ] Login page loads
- [ ] Assets load correctly (CSS, JS, images)
- [ ] Both themes work (modern and retro)

## Phase 6: Integration Testing

### 6.1 End-to-End Smoke Tests

**Test 1: User Authentication**
- [ ] Navigate to portal
- [ ] Click "Sign in with SSO"
- [ ] Redirected to Okta
- [ ] Enter credentials
- [ ] Redirected back to portal
- [ ] Dashboard loads successfully

**Test 2: WorkSpace Provisioning (Portal)**
- [ ] Navigate to Workspaces page
- [ ] Click "Provision WorkSpace"
- [ ] Select bundle type (STANDARD)
- [ ] Select blueprint
- [ ] Select OS (Windows)
- [ ] View cost estimate
- [ ] Click "Provision"
- [ ] WorkSpace appears in list with PENDING status
- [ ] Wait for AVAILABLE status (< 5 minutes)

**Test 3: WorkSpace Provisioning (CLI)**
```bash
forge launch --bundle STANDARD --os Windows --blueprint default
forge list
forge describe WORKSPACE_ID
```
- [ ] Provisioning succeeds
- [ ] WorkSpace appears in list
- [ ] Details display correctly

**Test 4: Lucy AI Chat**
- [ ] Open Lucy chat widget in portal
- [ ] Send message: "What workspaces do I have?"
- [ ] Lucy responds with workspace list
- [ ] Send message: "What's my current spend?"
- [ ] Lucy responds with cost information
- [ ] Send message: "I need a GPU workspace"
- [ ] Lucy provides recommendation and cost estimate

**Test 5: Cost Dashboard**
- [ ] Navigate to Costs page
- [ ] Verify cost summary displays
- [ ] Verify cost chart renders
- [ ] Verify recommendations appear
- [ ] Verify budget status shows correctly

**Test 6: Budget Enforcement**
- [ ] Set user budget to low value (via API or database)
- [ ] Attempt to provision workspace
- [ ] Verify warning at 80%
- [ ] Verify blocking at 100%
- [ ] Verify error message is clear

**Test 7: Theme Switching**
- [ ] Navigate to Settings
- [ ] Switch to Retro theme
- [ ] Verify scanlines and CRT effects
- [ ] Verify all pages render correctly
- [ ] Switch back to Modern theme
- [ ] Verify smooth animations

**Test 8: Accessibility**
- [ ] Test keyboard navigation (Tab, Enter, Escape)
- [ ] Test keyboard shortcuts (Ctrl+D, Ctrl+W, etc.)
- [ ] Test with screen reader (if available)
- [ ] Verify focus indicators visible
- [ ] Test reduced motion preference

### 6.2 Performance Testing
```bash
# Test API response time
curl -w "@curl-format.txt" -o /dev/null -s https://api.forge.staging.example.com/api/v1/workspaces

# Expected: < 500ms
```

**Verify:**
- [ ] API response time < 500ms
- [ ] Portal page load < 3 seconds
- [ ] Lucy response time < 2 seconds
- [ ] WebSocket connection stable

### 6.3 Security Testing

**Basic Security Checks:**
- [ ] HTTPS enforced (no HTTP access)
- [ ] Authentication required for all protected endpoints
- [ ] RBAC enforced (test with different roles)
- [ ] Secrets not exposed in logs or responses
- [ ] CORS configured correctly
- [ ] Security headers present (CSP, X-Frame-Options, etc.)

## Phase 7: Monitoring Setup

### 7.1 Verify Monitoring Stack
```bash
# Check Prometheus
kubectl port-forward -n forge-system svc/prometheus 9090:9090
# Open http://localhost:9090

# Check Grafana
kubectl port-forward -n forge-system svc/grafana 3000:3000
# Open http://localhost:3000
```

**Verify:**
- [ ] Prometheus collecting metrics
- [ ] Grafana dashboards available
- [ ] CloudWatch logs flowing
- [ ] Alerts configured

### 7.2 Test Alerting
```bash
# Trigger test alert
aws cloudwatch put-metric-data \
  --namespace Forge/API \
  --metric-name ErrorRate \
  --value 10 \
  --unit Percent
```

**Verify:**
- [ ] Alert triggers
- [ ] Notification received (email/Slack)
- [ ] Alert shows in Grafana

## Phase 8: Production Deployment

### 8.1 Production Readiness Review
- [ ] All staging tests passed
- [ ] Performance meets requirements
- [ ] Security review completed
- [ ] Disaster recovery plan documented
- [ ] Rollback plan documented
- [ ] On-call rotation established

### 8.2 Production Infrastructure
```bash
cd terraform/environments/production
terraform init
terraform plan -out=tfplan
# Review plan carefully
terraform apply tfplan
```

### 8.3 Production Secrets
```bash
# Use strong, unique passwords for production
aws secretsmanager create-secret --name forge/production/database --secret-string '...'
aws secretsmanager create-secret --name forge/production/anthropic --secret-string '...'
aws secretsmanager create-secret --name forge/production/okta --secret-string '...'
aws secretsmanager create-secret --name forge/production/jwt --secret-string '...'
```

### 8.4 Production Database
```bash
cd api
export DATABASE_URL="postgresql://forge:PASSWORD@PROD_RDS_ENDPOINT:5432/forge"
alembic upgrade head
python scripts/create_admin_user.py
python scripts/create_default_blueprints.py
```

### 8.5 Production API Deployment
```bash
# Build and push production image
docker build -t forge-api:v1.0.0 .
docker tag forge-api:v1.0.0 ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/forge-api:v1.0.0-prod
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/forge-api:v1.0.0-prod

# Deploy with blue/green strategy
kubectl apply -f k8s/production/api-deployment.yaml
kubectl rollout status deployment/forge-api -n forge-api
```

### 8.6 Production Portal Deployment
```bash
cd portal
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://api.forge.example.com
NEXT_PUBLIC_WS_URL=wss://api.forge.example.com/ws
EOF

npm run build
vercel --prod
```

### 8.7 Production Smoke Tests
- [ ] Repeat all smoke tests from Phase 6
- [ ] Verify production URLs work
- [ ] Verify SSL certificates valid
- [ ] Verify monitoring active

### 8.8 24-Hour Monitoring Period
- [ ] Monitor error rates (target: < 1%)
- [ ] Monitor response times (target: p95 < 500ms)
- [ ] Monitor provisioning success rate (target: > 99%)
- [ ] Monitor cost tracking accuracy
- [ ] No critical alerts

## Phase 9: User Onboarding

### 9.1 Create Initial Users
```bash
# Import users from CSV
python scripts/create_users.py --csv users.csv

# Assign roles
python scripts/assign_roles.py --user alice@example.com --role team_lead
python scripts/assign_roles.py --user bob@example.com --role engineer
```

### 9.2 Set Budgets
```bash
# Set team budgets
python scripts/set_budgets.py --team engineering --amount 10000
python scripts/set_budgets.py --team data-science --amount 15000

# Set user budgets
python scripts/set_budgets.py --user alice@example.com --amount 2000
```

### 9.3 User Training
- [ ] Distribute user guides (Portal, CLI, Lucy)
- [ ] Conduct training sessions
- [ ] Set up support channel (Slack/email)
- [ ] Share troubleshooting guide

## Post-Deployment

### Ongoing Monitoring
- [ ] Daily: Review CloudWatch alarms
- [ ] Daily: Check error logs
- [ ] Weekly: Review cost reports
- [ ] Weekly: Review utilization metrics
- [ ] Monthly: Security audit
- [ ] Monthly: Performance optimization review

### Maintenance Schedule
- [ ] Weekly: Dependency updates (security patches)
- [ ] Monthly: Infrastructure review
- [ ] Quarterly: Disaster recovery drill
- [ ] Quarterly: User feedback review

## Rollback Procedures

### API Rollback
```bash
kubectl rollout undo deployment/forge-api -n forge-api
kubectl rollout status deployment/forge-api -n forge-api
```

### Portal Rollback
```bash
vercel rollback
# Or for Kubernetes:
kubectl rollout undo deployment/forge-portal -n forge-portal
```

### Database Rollback
```bash
cd api
alembic downgrade -1
```

### Infrastructure Rollback
```bash
cd terraform/environments/production
terraform plan -destroy -out=tfplan
# Review carefully before applying
```

## Success Criteria

Deployment is considered successful when:
- [ ] All services healthy and accessible
- [ ] All smoke tests passing
- [ ] Error rate < 1%
- [ ] Response time p95 < 500ms
- [ ] Provisioning success rate > 99%
- [ ] No critical alerts for 24 hours
- [ ] Users successfully onboarded
- [ ] Documentation complete and accessible

## Support Contacts

- **Technical Lead**: _______________
- **Infrastructure Team**: _______________
- **Security Team**: _______________
- **On-Call Rotation**: _______________

## Notes

- This checklist should be completed in order
- Mark each item as complete before proceeding
- Document any issues or deviations
- Keep this checklist updated for future deployments

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Environment**: [ ] Staging [ ] Production
**Version**: v1.0.0
**Status**: [ ] In Progress [ ] Complete [ ] Rolled Back

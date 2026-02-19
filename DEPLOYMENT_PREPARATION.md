# RobCo Forge - Deployment Preparation Guide

**Created**: While Terraform is running (45 min wait)  
**Purpose**: Prepare everything needed for post-infrastructure deployment

---

## 📋 Table of Contents

1. [Next Steps Overview](#next-steps-overview)
2. [Secrets Preparation](#secrets-preparation)
3. [Local Environment Setup](#local-environment-setup)
4. [Architecture Review](#architecture-review)
5. [Post-Terraform Checklist](#post-terraform-checklist)

---

## Next Steps Overview

### What's Happening Now (45 minutes)
Terraform is creating:
- ✅ VPC with public/private subnets across 3 AZs
- ✅ EKS cluster with managed node groups
- ✅ RDS PostgreSQL (Multi-AZ)
- ⏳ **AWS Managed Microsoft AD** (Directory Service) - 40-45 min
- ⏳ FSx ONTAP filesystem (depends on Directory)
- ✅ Security groups and network policies
- ✅ CloudWatch log groups
- ✅ Monitoring infrastructure

### What Happens Next (After Terraform)
1. **Deploy Kubernetes Resources** (CDK) - 15 min
2. **Configure Secrets** (AWS Secrets Manager) - 10 min
3. **Setup Database** (Migrations) - 10 min
4. **Deploy API** (Docker + EKS) - 30 min
5. **Build CLI** (TypeScript) - 5 min
6. **Deploy Portal** (Vercel) - 15 min
7. **Run Smoke Tests** - 30 min

**Total Time After Terraform**: ~2 hours

---

## Secrets Preparation

### 1. Database Credentials

**What you need**: Strong password for PostgreSQL RDS

```bash
# Generate a strong password (or use your password manager)
openssl rand -base64 32

# Example output: xK9mP2vL8nQ4rT6wY1zA3bC5dE7fG9hJ0kM
```

**Store this securely** - you'll need it for:
- AWS Secrets Manager
- Database migrations
- API deployment

### 2. JWT Secret

**What you need**: Random string for signing JWT tokens

```bash
# Generate JWT secret
openssl rand -hex 32

# Example output: 4f8a2b6c9d1e3f5a7b9c0d2e4f6a8b0c1d3e5f7a9b0c2d4e6f8a0b2c4d6e8f0
```

### 3. Okta SSO Configuration

**What you need**: Okta SAML 2.0 application credentials

#### Step 1: Create Okta Application
1. Log into Okta Admin Console
2. Go to **Applications** → **Create App Integration**
3. Select **SAML 2.0**
4. Configure:
   - **App name**: RobCo Forge Staging
   - **Single sign on URL**: `https://api.forge.staging.example.com/api/v1/auth/callback`
   - **Audience URI**: `https://forge.staging.example.com`
   - **Name ID format**: EmailAddress
   - **Application username**: Email

#### Step 2: Get Credentials
After creating the app, note:
- **Client ID**: Found in app settings
- **Client Secret**: Found in app settings
- **Okta Domain**: Your Okta domain (e.g., `dev-12345.okta.com`)
- **Metadata URL**: Found in "Sign On" tab

#### Step 3: Assign Users
1. Go to **Assignments** tab
2. Assign yourself and test users
3. Assign groups if needed

### 4. Anthropic API Key

**What you need**: API key for Claude AI (Lucy service)

#### Option A: Anthropic Direct
1. Go to https://console.anthropic.com
2. Create account or log in
3. Go to **API Keys**
4. Create new key: "RobCo Forge Staging"
5. Copy the key (starts with `sk-ant-`)

#### Option B: AWS Bedrock
1. Go to AWS Console → Bedrock
2. Request access to Claude models
3. Wait for approval (can take 1-2 days)
4. Use AWS credentials instead of API key

**For now, use Option A** (Anthropic Direct) for faster setup.

### 5. Alert Email

**What you need**: Email address for CloudWatch alarms

Update in `terraform.tfvars`:
```hcl
alert_email_addresses = ["your-email@example.com"]
```

### Secrets Summary Checklist

Prepare these values now:

- [ ] Database password: `____________________`
- [ ] JWT secret: `____________________`
- [ ] Okta Client ID: `____________________`
- [ ] Okta Client Secret: `____________________`
- [ ] Okta Domain: `____________________`
- [ ] Anthropic API Key: `____________________`
- [ ] Alert email: `____________________`

---

## Local Environment Setup

### 1. API Local Development

#### Install Python Dependencies
```bash
cd api

# Create virtual environment
python3 -m venv venv

# Activate (Mac/Linux)
source venv/bin/activate

# Activate (Windows)
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Configure Environment
```bash
# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://forge:YOUR_PASSWORD@localhost:5432/forge
OKTA_METADATA_URL=https://YOUR_DOMAIN.okta.com/app/YOUR_APP_ID/sso/saml/metadata
JWT_SECRET_KEY=YOUR_JWT_SECRET
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY
EOF
```

#### Test Local API (Optional)
```bash
# Start local PostgreSQL (Docker)
docker run -d \
  --name forge-postgres \
  -e POSTGRES_USER=forge \
  -e POSTGRES_PASSWORD=forge \
  -e POSTGRES_DB=forge \
  -p 5432:5432 \
  postgres:15

# Run migrations
alembic upgrade head

# Start API
uvicorn src.main:app --reload

# Test
curl http://localhost:8000/health
```

### 2. CLI Local Development

#### Install Node Dependencies
```bash
cd cli

# Install dependencies
npm install

# Build
npm run build

# Test
npm run dev -- --help
```

#### Configure CLI
```bash
# After API is deployed, configure CLI
npm run dev -- config set apiUrl https://api.forge.staging.example.com
npm run dev -- config set authMethod okta
```

### 3. Portal Local Development (Optional)

```bash
cd portal

# Install dependencies
npm install

# Create .env.local
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
EOF

# Start dev server
npm run dev

# Open http://localhost:3000
```

---

## Architecture Review

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Users                                │
│  (Engineers, Team Leads, Contractors, Admins)               │
└────────────┬────────────────────────────┬───────────────────┘
             │                            │
             │                            │
    ┌────────▼────────┐          ┌───────▼────────┐
    │  Web Portal     │          │   CLI Tool     │
    │  (Vercel)       │          │  (Local)       │
    └────────┬────────┘          └───────┬────────┘
             │                            │
             └────────────┬───────────────┘
                          │
                 ┌────────▼────────┐
                 │   ALB (HTTPS)   │
                 └────────┬────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼─────┐    ┌────▼─────┐    ┌────▼─────┐
    │ Forge API│    │   Lucy   │    │   Cost   │
    │ (EKS Pod)│    │ (EKS Pod)│    │  Engine  │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼─────┐    ┌────▼─────┐    ┌────▼─────┐
    │   RDS    │    │  Redis   │    │   FSx    │
    │PostgreSQL│    │  Cache   │    │  ONTAP   │
    └──────────┘    └──────────┘    └────┬─────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
               ┌────▼─────┐         ┌────▼─────┐         ┌────▼─────┐
               │   AWS    │         │   AWS    │         │   AWS    │
               │WorkSpaces│         │WorkSpaces│         │WorkSpaces│
               │  (User1) │         │  (User2) │         │  (User3) │
               └──────────┘         └──────────┘         └──────────┘
```

### Network Architecture

```
VPC: 10.1.0.0/16 (Staging)

┌─────────────────────────────────────────────────────────────┐
│                         VPC                                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Public Subnets (3 AZs)                              │  │
│  │  - NAT Gateways                                      │  │
│  │  - Application Load Balancer                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Private Subnets - EKS (3 AZs)                       │  │
│  │  - EKS Worker Nodes                                  │  │
│  │  - API Pods                                          │  │
│  │  - Lucy Pods                                         │  │
│  │  - Cost Engine Pods                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Private Subnets - Data (3 AZs)                      │  │
│  │  - RDS PostgreSQL (Multi-AZ)                         │  │
│  │  - ElastiCache Redis                                 │  │
│  │  - FSx ONTAP                                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Private Subnets - WorkSpaces (2 AZs)                │  │
│  │  - AWS WorkSpaces Instances                          │  │
│  │  - No direct internet access                         │  │
│  │  - Access via FSx for user volumes                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Network Layer                                           │
│     - VPC isolation                                         │
│     - Security groups (least privilege)                     │
│     - Network ACLs                                          │
│     - Private subnets for sensitive resources               │
│                                                              │
│  2. Authentication Layer                                    │
│     - Okta SSO with SAML 2.0                               │
│     - MFA required                                          │
│     - JWT tokens (short-lived)                             │
│     - Refresh tokens (7-day expiry)                        │
│                                                              │
│  3. Authorization Layer                                     │
│     - RBAC (4 roles)                                       │
│     - Resource-level permissions                            │
│     - Team-based access control                            │
│     - Budget enforcement                                    │
│                                                              │
│  4. Data Layer                                              │
│     - Encryption at rest (AES-256)                         │
│     - Encryption in transit (TLS 1.3)                      │
│     - Secrets in AWS Secrets Manager                       │
│     - Database encryption                                   │
│                                                              │
│  5. Audit Layer                                             │
│     - Comprehensive audit logging                           │
│     - Tamper-evident storage                               │
│     - 7-year retention                                      │
│     - CloudTrail integration                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

#### Workspace Provisioning Flow
```
1. User → Portal/CLI → "Provision WorkSpace"
2. Portal/CLI → API → POST /api/v1/workspaces
3. API → Auth Check → Verify JWT token
4. API → RBAC Check → Verify permissions
5. API → Budget Check → Verify budget available
6. API → Cost Estimate → Calculate estimated cost
7. API → Pool Manager → Check pre-warmed pool
8. Pool Manager → AWS WorkSpaces API → Provision
9. AWS WorkSpaces → Active Directory → Domain join
10. FSx Service → Create user volume
11. FSx Service → Sync dotfiles from template
12. API → Database → Create workspace record
13. API → Audit Log → Log provisioning action
14. API → Response → Return workspace details
15. Portal/CLI → Display → Show workspace info
```

#### Cost Tracking Flow
```
1. Cost Engine (Cron: every 5 min)
2. Cost Engine → AWS Cost Explorer API
3. Cost Engine → Calculate per-workspace costs
4. Cost Engine → Database → Insert cost_records
5. Cost Engine → Aggregate by user/team/project
6. Cost Engine → Check budgets
7. Cost Engine → Generate alerts (if over 80%)
8. Cost Engine → CloudWatch → Publish metrics
```

#### Lucy AI Flow
```
1. User → Portal/CLI → "Ask Lucy"
2. Portal/CLI → API → POST /api/v1/lucy/chat
3. API → Context Manager → Load conversation history
4. API → Intent Recognizer → Classify intent
5. API → Tool Executor → Execute appropriate tool
6. Tool Executor → AWS APIs / Database
7. Tool Executor → Format results
8. API → Claude API → Generate natural response
9. API → Context Manager → Save conversation
10. API → Audit Log → Log Lucy interaction
11. API → Response → Return Lucy's message
12. Portal/CLI → Display → Show response
```

---

## Post-Terraform Checklist

### Immediate Actions (After Terraform Completes)

#### 1. Capture Terraform Outputs
```bash
cd terraform/environments/staging

# Get all outputs
terraform output -json > outputs.json

# Get specific values
terraform output eks_cluster_endpoint
terraform output rds_endpoint
terraform output fsx_filesystem_id
terraform output directory_id
```

**Save these values** - you'll need them for:
- Kubernetes configuration
- Database connection
- API deployment

#### 2. Configure kubectl
```bash
# Update kubeconfig
aws eks update-kubeconfig \
  --region us-east-1 \
  --name robco-forge-staging

# Verify connection
kubectl get nodes
kubectl get namespaces
```

#### 3. Deploy CDK Stacks
```bash
cd cdk

# Install dependencies
npm install

# Update cdk.context.json with Terraform outputs
# (Use values from terraform output)

# Deploy all stacks
cdk deploy --all --require-approval never

# Verify
kubectl get sa -A
kubectl get secrets -A
```

#### 4. Create Secrets in AWS Secrets Manager
```bash
# Database credentials
aws secretsmanager create-secret \
  --name forge/staging/database \
  --secret-string "{\"username\":\"forge\",\"password\":\"YOUR_DB_PASSWORD\"}" \
  --region us-east-1

# Anthropic API key
aws secretsmanager create-secret \
  --name forge/staging/anthropic \
  --secret-string "{\"api_key\":\"YOUR_ANTHROPIC_KEY\"}" \
  --region us-east-1

# Okta credentials
aws secretsmanager create-secret \
  --name forge/staging/okta \
  --secret-string "{\"client_id\":\"YOUR_CLIENT_ID\",\"client_secret\":\"YOUR_CLIENT_SECRET\",\"domain\":\"YOUR_DOMAIN.okta.com\"}" \
  --region us-east-1

# JWT secret
aws secretsmanager create-secret \
  --name forge/staging/jwt \
  --secret-string "{\"secret\":\"YOUR_JWT_SECRET\"}" \
  --region us-east-1

# Verify secrets created
aws secretsmanager list-secrets --region us-east-1
```

#### 5. Run Database Migrations
```bash
cd api

# Get RDS endpoint from Terraform output
export RDS_ENDPOINT=$(cd ../terraform/environments/staging && terraform output -raw rds_endpoint)

# Set DATABASE_URL
export DATABASE_URL="postgresql://forge:YOUR_DB_PASSWORD@${RDS_ENDPOINT}:5432/forge"

# Run migrations
alembic upgrade head

# Verify
alembic current
```

#### 6. Create Initial Data
```bash
# Still in api/ directory

# Create admin user
python scripts/create_admin_user.py

# Create default blueprints
python scripts/create_default_blueprints.py

# Verify
psql $DATABASE_URL -c "SELECT * FROM users;"
psql $DATABASE_URL -c "SELECT * FROM blueprints;"
```

### Next Phase: API Deployment

See **DEPLOYMENT_CHECKLIST.md** Phase 3 for detailed API deployment steps.

---

## Quick Reference Commands

### Check Terraform Status
```bash
cd terraform/environments/staging
terraform show
terraform output
```

### Check AWS Resources
```bash
# EKS Cluster
aws eks describe-cluster --name robco-forge-staging --region us-east-1

# RDS Instance
aws rds describe-db-instances --region us-east-1

# Directory Service
aws ds describe-directories --region us-east-1

# FSx Filesystem
aws fsx describe-file-systems --region us-east-1
```

### Check Kubernetes
```bash
# Nodes
kubectl get nodes

# Pods
kubectl get pods -A

# Services
kubectl get svc -A

# Secrets
kubectl get secrets -A
```

### Troubleshooting
```bash
# Terraform logs
export TF_LOG=DEBUG
terraform apply

# Kubernetes logs
kubectl logs -n kube-system -l app=aws-node

# RDS connectivity
psql "postgresql://forge:PASSWORD@RDS_ENDPOINT:5432/forge" -c "SELECT 1;"
```

---

## Estimated Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Terraform Infrastructure | 45-60 min | ⏳ In Progress |
| CDK Kubernetes Resources | 15 min | ⏸️ Waiting |
| Secrets Configuration | 10 min | ⏸️ Waiting |
| Database Setup | 10 min | ⏸️ Waiting |
| API Deployment | 30 min | ⏸️ Waiting |
| CLI Build | 5 min | ⏸️ Waiting |
| Portal Deployment | 15 min | ⏸️ Waiting |
| Smoke Tests | 30 min | ⏸️ Waiting |
| **Total** | **2.5-3 hours** | |

---

## Success Criteria

You'll know you're ready to proceed when:

- ✅ Terraform completes without errors
- ✅ All secrets prepared and documented
- ✅ Local environment set up (API + CLI)
- ✅ Architecture understood
- ✅ kubectl configured and working
- ✅ Next steps clear

---

## Need Help?

- **Terraform Issues**: See TROUBLESHOOTING.md
- **AWS Issues**: Check CloudTrail logs
- **Secrets Issues**: Verify IAM permissions
- **Next Steps**: See DEPLOYMENT_CHECKLIST.md

---

**Status**: Waiting for Terraform to complete...  
**Next**: Run Post-Terraform Checklist above


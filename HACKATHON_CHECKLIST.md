# RobCo Forge - Hackathon Quick Start

## Pre-Deployment (5 minutes)

- [ ] AWS credentials are valid and refreshed
- [ ] Update `terraform/environments/production/terraform.tfvars`:
  - [ ] Change `alert_email_addresses`
  - [ ] Change `directory_password` (min 8 chars, uppercase, lowercase, number, special char)
  - [ ] Change `active_directory_password` (same as directory_password)

## Deploy Infrastructure (45-60 minutes)

```bash
cd terraform/environments/production
terraform init
terraform plan
terraform apply
```

- [ ] Terraform init successful
- [ ] Terraform plan shows ~35 resources to create
- [ ] Terraform apply started
- [ ] ☕ Take a break (45-60 min wait)

## Post-Deployment (2 hours)

### 1. Capture Outputs (2 min)
```bash
terraform output -json > outputs.json
```

### 2. Configure kubectl (2 min)
```bash
aws eks update-kubeconfig --region us-east-1 --name robco-forge-production
kubectl get nodes
```

### 3. Deploy Kubernetes Resources (15 min)
```bash
cd ../../cdk
npm install
cdk deploy --all
```

### 4. Create Secrets (10 min)
```bash
# Generate secrets
openssl rand -base64 32  # DB password
openssl rand -hex 32     # JWT secret

# Create in AWS Secrets Manager
aws secretsmanager create-secret --name forge/production/database --secret-string '{"username":"forge","password":"YOUR_DB_PASSWORD"}'
aws secretsmanager create-secret --name forge/production/jwt --secret-string '{"secret":"YOUR_JWT_SECRET"}'
aws secretsmanager create-secret --name forge/production/anthropic --secret-string '{"api_key":"YOUR_ANTHROPIC_KEY"}'
```

### 5. Database Setup (10 min)
```bash
cd ../api
export DATABASE_URL="postgresql://forge:PASSWORD@RDS_ENDPOINT:5432/forge"
alembic upgrade head
```

### 6. Deploy API (30 min)
```bash
# Build Docker image
docker build -t robco-forge-api .

# Push to ECR
# Deploy to EKS
```

### 7. Deploy Portal (15 min)
```bash
cd ../portal
vercel deploy --prod
```

### 8. Smoke Tests (30 min)
- [ ] API health check
- [ ] Database connectivity
- [ ] Authentication flow
- [ ] Provision test WorkSpace
- [ ] Lucy AI interaction

## Hackathon Demo Ready! 🎉

Total time: ~3 hours from start to demo-ready

## Cleanup After Hackathon

```bash
cd terraform/environments/production
terraform destroy
```

Cost for 48 hours: ~$62

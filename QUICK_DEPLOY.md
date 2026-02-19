# RobCo Forge - Quick Deploy Reference

## 🚀 Deploy in 5 Steps

### Step 1: Prerequisites (5 minutes)
```bash
# Verify tools installed
terraform version  # >= 1.5.0
aws --version      # >= 2.0
kubectl version    # >= 1.27
node --version     # >= 18.0
python3 --version  # >= 3.11
docker --version   # >= 24.0

# Configure AWS
aws configure
```

### Step 2: Deploy Infrastructure (30-60 minutes)
```bash
# Option A: Automated
chmod +x deploy.sh
./deploy.sh staging v1.0.0
# Select option 2 (Infrastructure only)

# Option B: Manual
cd terraform/environments/staging
terraform init
terraform plan -out=tfplan
terraform apply tfplan

cd ../../../cdk
npm install
cdk deploy --all --require-approval never
```

### Step 3: Configure Secrets (5 minutes)
```bash
# Update these with real values!
aws secretsmanager create-secret \
  --name forge/staging/database \
  --secret-string '{"username":"forge","password":"YOUR_STRONG_PASSWORD"}'

aws secretsmanager create-secret \
  --name forge/staging/anthropic \
  --secret-string '{"api_key":"YOUR_ANTHROPIC_KEY"}'

aws secretsmanager create-secret \
  --name forge/staging/okta \
  --secret-string '{"client_id":"YOUR_OKTA_ID","client_secret":"YOUR_OKTA_SECRET","domain":"YOUR_OKTA_DOMAIN"}'

aws secretsmanager create-secret \
  --name forge/staging/jwt \
  --secret-string '{"secret":"YOUR_RANDOM_32_CHAR_STRING"}'
```

### Step 4: Deploy Services (30-45 minutes)
```bash
# Database
cd api
pip install -r requirements.txt
export DATABASE_URL="postgresql://forge:PASSWORD@RDS_ENDPOINT:5432/forge"
alembic upgrade head
python scripts/create_admin_user.py

# API
docker build -t forge-api:v1.0.0 .
# Push to ECR and deploy (see DEPLOYMENT_GUIDE.md)

# CLI
cd ../cli
npm install && npm run build && npm pack

# Portal
cd ../portal
npm install
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://api.forge.staging.example.com
NEXT_PUBLIC_WS_URL=wss://api.forge.staging.example.com/ws
EOF
npm run build
vercel --prod  # Or your preferred deployment method
```

### Step 5: Verify (15 minutes)
```bash
# Test API
curl https://api.forge.staging.example.com/health

# Test CLI
npm install -g ./cli/forge-cli-1.0.0.tgz
forge config set api-url https://api.forge.staging.example.com
forge login

# Test Portal
# Open https://portal.forge.staging.example.com
# Login with SSO
# Provision a test workspace
```

---

## 📋 Essential URLs

After deployment, bookmark these:

- **Portal**: https://portal.forge.staging.example.com
- **API Docs**: https://api.forge.staging.example.com/docs
- **Grafana**: http://localhost:3000 (port-forward)
- **Prometheus**: http://localhost:9090 (port-forward)

---

## 🔑 Required Secrets

Before deploying, have these ready:

1. **Database Password**: Strong, unique, 16+ characters
2. **JWT Secret**: Random string, 32+ characters
3. **Okta Credentials**: Client ID, Secret, Domain
4. **Anthropic API Key**: From Anthropic console
5. **AWS Credentials**: Access key with appropriate permissions

---

## ⚡ Quick Commands

### Check Status
```bash
# Infrastructure
terraform output -json

# Kubernetes
kubectl get pods -A
kubectl get ingress -A

# API
kubectl logs -n forge-api -l app=forge-api --tail=50

# Database
kubectl exec -it -n forge-api <pod-name> -- python -c "from src.database import engine; engine.connect()"
```

### Troubleshooting
```bash
# View logs
kubectl logs -n forge-api -l app=forge-api --tail=100 -f

# Restart pods
kubectl rollout restart deployment/forge-api -n forge-api

# Check secrets
kubectl get secrets -n forge-api

# Port forward Grafana
kubectl port-forward -n forge-system svc/grafana 3000:3000
```

### Rollback
```bash
# API
kubectl rollout undo deployment/forge-api -n forge-api

# Portal (Vercel)
vercel rollback

# Database
cd api && alembic downgrade -1

# Infrastructure
cd terraform/environments/staging
terraform destroy
```

---

## 🎯 Success Checklist

- [ ] Infrastructure deployed (VPC, EKS, RDS, FSx)
- [ ] Secrets configured in AWS Secrets Manager
- [ ] Database migrations completed
- [ ] API pods running (3 replicas)
- [ ] CLI built and packaged
- [ ] Portal deployed and accessible
- [ ] Health check returns 200
- [ ] Can login with SSO
- [ ] Can provision workspace
- [ ] Lucy responds to messages
- [ ] Cost dashboard shows data
- [ ] Both themes work (modern + retro)

---

## 🆘 Emergency Contacts

- **Deployment Issues**: Check DEPLOYMENT_GUIDE.md
- **Infrastructure Issues**: Check Terraform logs
- **Application Issues**: Check CloudWatch logs
- **Security Issues**: Review RBAC and secrets

---

## 📚 Full Documentation

- **Complete Guide**: DEPLOYMENT_GUIDE.md
- **Detailed Checklist**: DEPLOYMENT_CHECKLIST.md
- **Project Overview**: PROJECT_SUMMARY.md
- **Deployment Ready**: DEPLOYMENT_READY.md

---

## 💡 Pro Tips

1. **Start with staging** - Never deploy directly to production
2. **Test thoroughly** - Run all smoke tests before declaring success
3. **Monitor closely** - Watch logs and metrics for first 24 hours
4. **Document changes** - Keep notes of any deviations from plan
5. **Have rollback ready** - Know how to rollback before deploying

---

## 🎉 You're Ready!

Everything is built and documented. Choose your path:

**Quick Start**: `./deploy.sh staging v1.0.0`  
**Manual**: Follow DEPLOYMENT_CHECKLIST.md  
**Phased**: Deploy staging first, then production

Good luck! 🚀

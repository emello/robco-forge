# RobCo Forge - Domain Setup Guide (robcoforge.com)

## Domain Structure

### Staging Environment
- **Portal**: `staging.robcoforge.com`
- **API**: `api-staging.robcoforge.com`
- **WebSocket**: `wss://api-staging.robcoforge.com/ws`

### Production Environment
- **Portal**: `robcoforge.com` (or `portal.robcoforge.com`)
- **API**: `api.robcoforge.com`
- **WebSocket**: `wss://api.robcoforge.com/ws`

---

## Setup Steps

### 1. DNS Configuration (Do This First)

#### Option A: Using Route 53 (Recommended for AWS)

```bash
# Create hosted zone for robcoforge.com
aws route53 create-hosted-zone \
  --name robcoforge.com \
  --caller-reference $(date +%s) \
  --hosted-zone-config Comment="RobCo Forge domain"

# Get the nameservers
aws route53 get-hosted-zone --id <HOSTED_ZONE_ID> \
  --query 'DelegationSet.NameServers' \
  --output table
```

**Then**: Update your domain registrar (where you bought robcoforge.com) with these Route 53 nameservers.

#### Option B: Using Your Current DNS Provider

If you want to keep your current DNS provider, you'll add CNAME records later (see step 4).

---

### 2. SSL Certificates (AWS Certificate Manager)

```bash
# Request wildcard certificate for all subdomains
aws acm request-certificate \
  --domain-name "*.robcoforge.com" \
  --subject-alternative-names "robcoforge.com" \
  --validation-method DNS \
  --region us-east-1

# Get certificate ARN
aws acm list-certificates --region us-east-1

# Get validation records
aws acm describe-certificate \
  --certificate-arn <CERTIFICATE_ARN> \
  --region us-east-1 \
  --query 'Certificate.DomainValidationOptions[*].[DomainName,ResourceRecord]' \
  --output table
```

**Add the DNS validation records** to Route 53 or your DNS provider.

**Wait for validation** (usually 5-30 minutes):
```bash
aws acm describe-certificate \
  --certificate-arn <CERTIFICATE_ARN> \
  --region us-east-1 \
  --query 'Certificate.Status'
```

---

### 3. Update Okta SSO Configuration

In your Okta Admin Console:

1. Go to your RobCo Forge application
2. Update **Single Sign-On URL**: 
   - Staging: `https://api-staging.robcoforge.com/api/v1/auth/callback`
   - Production: `https://api.robcoforge.com/api/v1/auth/callback`
3. Update **Audience URI**:
   - Staging: `https://staging.robcoforge.com`
   - Production: `https://robcoforge.com`
4. Save changes

---

### 4. Deploy Portal to Vercel with Custom Domain

```bash
cd portal

# Deploy to Vercel
vercel --prod

# In Vercel Dashboard:
# 1. Go to your project settings
# 2. Click "Domains"
# 3. Add custom domain: staging.robcoforge.com
# 4. Vercel will provide DNS records to add

# Add the CNAME record to your DNS:
# Type: CNAME
# Name: staging
# Value: cname.vercel-dns.com (or whatever Vercel provides)
```

**Vercel handles SSL automatically** - no need to use the ACM certificate for the portal.

---

### 5. Configure API Domain (After EKS Deployment)

After your EKS cluster and API are deployed:

```bash
# Get the Application Load Balancer DNS name
kubectl get ingress -n forge-api -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}'

# Example output: abc123-1234567890.us-east-1.elb.amazonaws.com
```

#### Option A: Using Route 53

```bash
# Create CNAME record for API
aws route53 change-resource-record-sets \
  --hosted-zone-id <YOUR_ZONE_ID> \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api-staging.robcoforge.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "YOUR-ALB-DNS-NAME"}]
      }
    }]
  }'
```

#### Option B: Using Your DNS Provider

Add a CNAME record:
- **Type**: CNAME
- **Name**: api-staging
- **Value**: YOUR-ALB-DNS-NAME (from kubectl command above)
- **TTL**: 300

---

### 6. Update API Ingress for SSL

After getting your ACM certificate, update the API ingress to use it:

```bash
# Edit the ingress to add SSL certificate annotation
kubectl edit ingress -n forge-api

# Add these annotations:
metadata:
  annotations:
    alb.ingress.kubernetes.io/certificate-arn: <YOUR_ACM_CERTIFICATE_ARN>
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
```

Or update your Kubernetes manifest file and reapply.

---

## Configuration File Updates

### 1. Terraform Variables (terraform.tfvars)

No changes needed! The domain is only used for external access, not infrastructure.

### 2. Portal Environment Variables

Update `portal/.env.production`:

```bash
# For Staging
NEXT_PUBLIC_API_URL=https://api-staging.robcoforge.com
NEXT_PUBLIC_WS_URL=wss://api-staging.robcoforge.com/ws

# For Production
NEXT_PUBLIC_API_URL=https://api.robcoforge.com
NEXT_PUBLIC_WS_URL=wss://api.robcoforge.com/ws
```

### 3. CLI Configuration

Users will configure the CLI to use the domain:

```bash
# Staging
forge config set apiUrl https://api-staging.robcoforge.com

# Production
forge config set apiUrl https://api.robcoforge.com
```

### 4. API Environment Variables

Update `api/.env` (or Kubernetes secrets):

```bash
# For Staging
API_BASE_URL=https://api-staging.robcoforge.com
CORS_ORIGINS=["https://staging.robcoforge.com"]

# For Production
API_BASE_URL=https://api.robcoforge.com
CORS_ORIGINS=["https://robcoforge.com","https://portal.robcoforge.com"]
```

### 5. Secrets Template

Update `SECRETS_TEMPLATE.md` with the new Okta URLs (already covered in step 3).

---

## Verification Checklist

After setup, verify everything works:

### DNS Resolution
```bash
# Check DNS propagation
dig staging.robcoforge.com
dig api-staging.robcoforge.com

# Should resolve to:
# staging.robcoforge.com -> Vercel IP
# api-staging.robcoforge.com -> ALB DNS name
```

### SSL Certificates
```bash
# Check SSL certificate
curl -vI https://staging.robcoforge.com 2>&1 | grep -i "subject:"
curl -vI https://api-staging.robcoforge.com 2>&1 | grep -i "subject:"

# Should show valid certificates for *.robcoforge.com
```

### API Health Check
```bash
curl https://api-staging.robcoforge.com/health

# Should return: {"status": "healthy"}
```

### Portal Access
```bash
# Open in browser
open https://staging.robcoforge.com

# Should load the portal
```

### Okta SSO
1. Go to https://staging.robcoforge.com
2. Click "Sign in with SSO"
3. Should redirect to Okta
4. After login, should redirect back to portal

---

## Timeline

| Task | Time | When |
|------|------|------|
| Create Route 53 hosted zone | 5 min | Now |
| Update domain registrar nameservers | 5 min | Now (propagation: 1-48 hours) |
| Request ACM certificate | 5 min | Now |
| Add DNS validation records | 5 min | Now |
| Wait for certificate validation | 5-30 min | Now |
| Update Okta configuration | 5 min | Now |
| Deploy portal to Vercel | 10 min | After portal is built |
| Add custom domain in Vercel | 5 min | After portal deployed |
| Configure API domain | 10 min | After EKS deployed |
| Update API ingress for SSL | 5 min | After API deployed |
| **Total active time** | **~1 hour** | |
| **Total wait time** | **1-48 hours** | (DNS propagation) |

---

## Quick Start Commands

```bash
# 1. Create Route 53 hosted zone
aws route53 create-hosted-zone --name robcoforge.com --caller-reference $(date +%s)

# 2. Request SSL certificate
aws acm request-certificate \
  --domain-name "*.robcoforge.com" \
  --subject-alternative-names "robcoforge.com" \
  --validation-method DNS \
  --region us-east-1

# 3. Get validation records and add to DNS
aws acm describe-certificate --certificate-arn <ARN> --region us-east-1

# 4. Update Okta (manual in Okta console)

# 5. Deploy portal (after it's built)
cd portal
vercel --prod
# Add staging.robcoforge.com in Vercel dashboard

# 6. Configure API domain (after EKS deployed)
kubectl get ingress -n forge-api
# Add CNAME: api-staging.robcoforge.com -> ALB DNS
```

---

## Troubleshooting

### DNS Not Resolving
- **Check nameservers**: `dig NS robcoforge.com`
- **Wait for propagation**: Can take up to 48 hours
- **Use DNS checker**: https://dnschecker.org

### SSL Certificate Not Validating
- **Check DNS records**: Ensure validation CNAME is added correctly
- **Wait**: Can take up to 30 minutes
- **Check status**: `aws acm describe-certificate --certificate-arn <ARN>`

### Okta Redirect Not Working
- **Check callback URL**: Must match exactly (including https://)
- **Check CORS**: API must allow portal domain
- **Check browser console**: Look for CORS or redirect errors

### Portal Not Loading
- **Check Vercel deployment**: `vercel ls`
- **Check DNS**: `dig staging.robcoforge.com`
- **Check SSL**: `curl -vI https://staging.robcoforge.com`

### API Not Accessible
- **Check ALB**: `kubectl get ingress -n forge-api`
- **Check DNS**: `dig api-staging.robcoforge.com`
- **Check SSL certificate**: Ensure ACM cert is attached to ALB
- **Check security groups**: ALB must allow inbound 443

---

## Production Deployment

When ready for production, repeat the same steps but use:
- `robcoforge.com` (or `portal.robcoforge.com`) for portal
- `api.robcoforge.com` for API
- Update Okta with production URLs
- Deploy to production environment

---

## Cost Estimate

- **Route 53 Hosted Zone**: $0.50/month
- **ACM Certificate**: Free
- **Vercel (Hobby)**: Free (or $20/month for Pro)
- **DNS Queries**: ~$0.40/month per million queries

**Total**: ~$1-21/month depending on Vercel plan

---

## Next Steps

1. ✅ Create Route 53 hosted zone
2. ✅ Update domain registrar nameservers
3. ✅ Request ACM certificate
4. ✅ Update Okta configuration
5. ⏸️ Wait for Terraform to complete
6. ⏸️ Deploy portal to Vercel
7. ⏸️ Configure API domain after EKS deployment

---

**Domain**: robcoforge.com  
**Environment**: Staging  
**Status**: Ready to configure


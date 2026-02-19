# RobCo Forge - Secrets Template

**Purpose**: Track all secrets needed for deployment  
**Security**: DO NOT commit this file with real values!

---

## Secrets Checklist

### 1. Database Credentials
```bash
# Generate strong password
openssl rand -base64 32
```

- **Username**: `forge` (default)
- **Password**: `________________________________`
- **Used in**:
  - AWS Secrets Manager: `forge/staging/database`
  - Database migrations
  - API deployment

---

### 2. JWT Configuration
```bash
# Generate JWT secret
openssl rand -hex 32
```

- **Secret**: `________________________________`
- **Algorithm**: `HS256` (default)
- **Access Token Expiry**: `60 minutes` (default)
- **Refresh Token Expiry**: `7 days` (default)
- **Used in**:
  - AWS Secrets Manager: `forge/staging/jwt`
  - API authentication

---

### 3. Okta SSO Configuration

#### Application Details
- **App Name**: RobCo Forge Staging
- **App Type**: SAML 2.0
- **Single Sign-On URL**: `https://api.forge.staging.example.com/api/v1/auth/callback`
- **Audience URI**: `https://forge.staging.example.com`

#### Update Okta Configuration
When you set up Okta SSO, use:
- **Single Sign-On URL**: `https://api-staging.robcoforge.com/api/v1/auth/callback`
- **Audience URI**: `https://staging.robcoforge.com`

#### Credentials
- **Client ID**: `________________________________`
- **Client Secret**: `________________________________`
- **Okta Domain**: `________________________________.okta.com`
- **Metadata URL**: `https://________________________________.okta.com/app/____________/sso/saml/metadata`

#### Used in
- AWS Secrets Manager: `forge/staging/okta`
- API authentication
- Portal SSO

---

### 4. Anthropic API Key

#### Option A: Anthropic Direct (Recommended for Quick Start)
- **API Key**: `sk-ant-________________________________`
- **Get from**: https://console.anthropic.com
- **Rate Limits**: Check your plan

#### Option B: AWS Bedrock (For Production)
- **Region**: `us-east-1`
- **Model**: `anthropic.claude-3-sonnet-20240229-v1:0`
- **Access**: Request via AWS Console → Bedrock

#### Used in
- AWS Secrets Manager: `forge/staging/anthropic`
- Lucy AI service

---

### 5. Alert Configuration

- **Email Address**: `________________________________`
- **Used for**: CloudWatch alarms, budget alerts
- **Update in**: `terraform/environments/staging/terraform.tfvars`

---

### 6. Domain Configuration (Optional)

If using custom domains:

- **API Domain**: `api.forge.staging.example.com`
- **Portal Domain**: `portal.forge.staging.example.com`
- **SSL Certificate**: AWS ACM or Let's Encrypt

---

## AWS Secrets Manager Commands

### Create All Secrets

```bash
# Set your values here
DB_PASSWORD="YOUR_DB_PASSWORD"
JWT_SECRET="YOUR_JWT_SECRET"
OKTA_CLIENT_ID="YOUR_OKTA_CLIENT_ID"
OKTA_CLIENT_SECRET="YOUR_OKTA_CLIENT_SECRET"
OKTA_DOMAIN="YOUR_OKTA_DOMAIN"
ANTHROPIC_API_KEY="YOUR_ANTHROPIC_KEY"

# Create database secret
aws secretsmanager create-secret \
  --name forge/staging/database \
  --secret-string "{\"username\":\"forge\",\"password\":\"${DB_PASSWORD}\"}" \
  --region us-east-1

# Create JWT secret
aws secretsmanager create-secret \
  --name forge/staging/jwt \
  --secret-string "{\"secret\":\"${JWT_SECRET}\"}" \
  --region us-east-1

# Create Okta secret
aws secretsmanager create-secret \
  --name forge/staging/okta \
  --secret-string "{\"client_id\":\"${OKTA_CLIENT_ID}\",\"client_secret\":\"${OKTA_CLIENT_SECRET}\",\"domain\":\"${OKTA_DOMAIN}\"}" \
  --region us-east-1

# Create Anthropic secret
aws secretsmanager create-secret \
  --name forge/staging/anthropic \
  --secret-string "{\"api_key\":\"${ANTHROPIC_API_KEY}\"}" \
  --region us-east-1
```

### Verify Secrets

```bash
# List all secrets
aws secretsmanager list-secrets --region us-east-1 | grep forge/staging

# Get specific secret (for testing)
aws secretsmanager get-secret-value \
  --secret-id forge/staging/database \
  --region us-east-1 \
  --query SecretString \
  --output text
```

### Update Secrets (If Needed)

```bash
# Update database password
aws secretsmanager update-secret \
  --secret-id forge/staging/database \
  --secret-string "{\"username\":\"forge\",\"password\":\"NEW_PASSWORD\"}" \
  --region us-east-1
```

---

## Environment Variables for Local Development

### API (.env)
```bash
DATABASE_URL=postgresql://forge:YOUR_DB_PASSWORD@localhost:5432/forge
OKTA_METADATA_URL=https://YOUR_DOMAIN.okta.com/app/YOUR_APP_ID/sso/saml/metadata
OKTA_SP_ENTITY_ID=https://forge.staging.example.com
OKTA_SP_ACS_URL=https://forge.staging.example.com/api/v1/auth/callback
JWT_SECRET_KEY=YOUR_JWT_SECRET
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY
AWS_REGION=us-east-1
```

### CLI (.env)
```bash
FORGE_API_URL=https://api.forge.staging.example.com
FORGE_AUTH_METHOD=okta
```

### Portal (.env.production)
```bash
NEXT_PUBLIC_API_URL=https://api.forge.staging.example.com
NEXT_PUBLIC_WS_URL=wss://api.forge.staging.example.com/ws
```

---

## Security Best Practices

### Password Requirements
- ✅ Minimum 16 characters
- ✅ Mix of uppercase, lowercase, numbers, symbols
- ✅ No dictionary words
- ✅ Unique per environment (staging ≠ production)
- ✅ Stored in password manager

### Secret Rotation
- 🔄 Database password: Every 90 days
- 🔄 JWT secret: Every 180 days
- 🔄 API keys: Every 365 days or on compromise
- 🔄 Okta credentials: On personnel changes

### Access Control
- 🔒 Limit AWS Secrets Manager access to deployment role
- 🔒 Use IAM policies for least-privilege access
- 🔒 Enable CloudTrail logging for secret access
- 🔒 Set up alerts for secret access

---

## Validation Checklist

Before proceeding with deployment:

- [ ] All secrets generated with sufficient entropy
- [ ] Secrets stored in password manager
- [ ] AWS Secrets Manager secrets created
- [ ] Okta application configured and tested
- [ ] Anthropic API key validated
- [ ] Alert email confirmed
- [ ] Local .env files created (for development)
- [ ] This file NOT committed to git

---

## Troubleshooting

### Secret Not Found
```bash
# Check if secret exists
aws secretsmanager describe-secret \
  --secret-id forge/staging/database \
  --region us-east-1
```

### Permission Denied
```bash
# Check IAM permissions
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR_USERNAME
```

### Okta Connection Failed
- Verify callback URLs match exactly
- Check Okta application is assigned to users
- Verify metadata URL is accessible
- Check Okta domain is correct

### Anthropic API Key Invalid
- Verify key starts with `sk-ant-`
- Check key hasn't expired
- Verify account has API access enabled
- Test key with curl:
```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-sonnet-20240229","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}'
```

---

## Next Steps

After completing this template:

1. ✅ Generate all secrets
2. ✅ Store in password manager
3. ✅ Create AWS Secrets Manager secrets
4. ✅ Verify secrets are accessible
5. ➡️ Proceed to database migrations (DEPLOYMENT_PREPARATION.md)

---

**Last Updated**: _______________  
**Updated By**: _______________  
**Environment**: Staging


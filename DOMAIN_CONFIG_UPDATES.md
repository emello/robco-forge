# Domain Configuration Updates for robcoforge.com

## Files to Update After Deployment

### 1. Portal Environment Variables

Create `portal/.env.production`:

```bash
# Staging
NEXT_PUBLIC_API_URL=https://api-staging.robcoforge.com
NEXT_PUBLIC_WS_URL=wss://api-staging.robcoforge.com/ws
```

Create `portal/.env.production.local` for production:

```bash
# Production
NEXT_PUBLIC_API_URL=https://api.robcoforge.com
NEXT_PUBLIC_WS_URL=wss://api.robcoforge.com/ws
```

### 2. API Environment Variables

Update `api/.env` or Kubernetes ConfigMap:

```bash
# Staging
API_BASE_URL=https://api-staging.robcoforge.com
CORS_ORIGINS=["https://staging.robcoforge.com","http://localhost:3000"]

# Production
API_BASE_URL=https://api.robcoforge.com
CORS_ORIGINS=["https://robcoforge.com","https://portal.robcoforge.com"]
```

### 3. CLI Default Configuration

Update `cli/.env.example`:

```bash
# Staging
FORGE_API_URL=https://api-staging.robcoforge.com

# Production
FORGE_API_URL=https://api.robcoforge.com
```

### 4. Okta SSO Configuration

**Staging Application:**
- Single Sign-On URL: `https://api-staging.robcoforge.com/api/v1/auth/callback`
- Audience URI: `https://staging.robcoforge.com`
- Logout URL: `https://api-staging.robcoforge.com/api/v1/auth/logout`

**Production Application:**
- Single Sign-On URL: `https://api.robcoforge.com/api/v1/auth/callback`
- Audience URI: `https://robcoforge.com`
- Logout URL: `https://api.robcoforge.com/api/v1/auth/logout`

### 5. README.md Updates

Update all example URLs in README.md:

```markdown
# Old
https://api.forge.staging.example.com
https://portal.forge.staging.example.com

# New
https://api-staging.robcoforge.com
https://staging.robcoforge.com
```

### 6. Deployment Documentation

Update DEPLOYMENT_GUIDE.md, DEPLOYMENT_PREPARATION.md, etc. with new URLs.

---

## Quick Reference

### Staging URLs
- Portal: https://staging.robcoforge.com
- API: https://api-staging.robcoforge.com
- API Docs: https://api-staging.robcoforge.com/docs
- WebSocket: wss://api-staging.robcoforge.com/ws

### Production URLs
- Portal: https://robcoforge.com
- API: https://api.robcoforge.com
- API Docs: https://api.robcoforge.com/docs
- WebSocket: wss://api.robcoforge.com/ws

---

## When to Apply These Changes

1. **Now**: Update Okta configuration
2. **After Portal Build**: Create .env.production files
3. **After API Deployment**: Update API environment variables
4. **After EKS Deployment**: Configure DNS and SSL

---

## Commands to Run

```bash
# Create portal environment file
cat > portal/.env.production << EOF
NEXT_PUBLIC_API_URL=https://api-staging.robcoforge.com
NEXT_PUBLIC_WS_URL=wss://api-staging.robcoforge.com/ws
EOF

# Create API environment file (or update Kubernetes secret)
cat > api/.env.staging << EOF
API_BASE_URL=https://api-staging.robcoforge.com
CORS_ORIGINS=["https://staging.robcoforge.com"]
EOF

# Update CLI default
cat > cli/.env.example << EOF
FORGE_API_URL=https://api-staging.robcoforge.com
FORGE_DEFAULT_BUNDLE=PERFORMANCE
FORGE_DEFAULT_OS=Linux
FORGE_OUTPUT_FORMAT=table
EOF
```


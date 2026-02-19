# 🌐 RobCo Forge API - Public Access

**Status**: ✅ LIVE AND ACCESSIBLE

---

## Public API URL

```
http://a5778e36f7e224c0fa8564d322f5a8bd-977c9e9765e61656.elb.us-east-1.amazonaws.com
```

---

## Quick Test

```bash
# Health check
curl http://a5778e36f7e224c0fa8564d322f5a8bd-977c9e9765e61656.elb.us-east-1.amazonaws.com/health

# API info
curl http://a5778e36f7e224c0fa8564d322f5a8bd-977c9e9765e61656.elb.us-east-1.amazonaws.com/

# API Documentation (open in browser)
http://a5778e36f7e224c0fa8564d322f5a8bd-977c9e9765e61656.elb.us-east-1.amazonaws.com/api/docs
```

---

## Available Endpoints

### Public Endpoints
- `GET /` - API information
- `GET /health` - Health check
- `GET /health/live` - Liveness check
- `GET /api/docs` - Interactive API documentation (Swagger UI)
- `GET /api/redoc` - Alternative API documentation (ReDoc)
- `GET /metrics` - Prometheus metrics

### API Endpoints (v1)
All API endpoints are prefixed with `/api/v1/`

**Authentication** (currently disabled):
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/refresh` - Refresh token

**WorkSpaces**:
- `GET /api/v1/workspaces` - List workspaces
- `POST /api/v1/workspaces` - Create workspace
- `GET /api/v1/workspaces/{id}` - Get workspace details
- `DELETE /api/v1/workspaces/{id}` - Terminate workspace

**Blueprints**:
- `GET /api/v1/blueprints` - List blueprints
- `POST /api/v1/blueprints` - Create blueprint
- `GET /api/v1/blueprints/{id}` - Get blueprint details

**Cost Tracking**:
- `GET /api/v1/costs` - Get cost data
- `GET /api/v1/costs/summary` - Cost summary

**Budgets**:
- `GET /api/v1/budgets` - List budgets
- `POST /api/v1/budgets` - Create budget

**Audit Logs**:
- `GET /api/v1/audit` - Query audit logs

---

## Testing with curl

### Health Check
```bash
curl http://a5778e36f7e224c0fa8564d322f5a8bd-977c9e9765e61656.elb.us-east-1.amazonaws.com/health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "forge-api",
  "version": "1.0.0"
}
```

### API Information
```bash
curl http://a5778e36f7e224c0fa8564d322f5a8bd-977c9e9765e61656.elb.us-east-1.amazonaws.com/
```

**Response**:
```json
{
  "service": "RobCo Forge API",
  "version": "1.0.0",
  "docs": "/api/docs",
  "health": "/health",
  "metrics": "/metrics"
}
```

---

## Interactive Documentation

Open in your browser:

**Swagger UI** (recommended):
```
http://a5778e36f7e224c0fa8564d322f5a8bd-977c9e9765e61656.elb.us-east-1.amazonaws.com/api/docs
```

**ReDoc**:
```
http://a5778e36f7e224c0fa8564d322f5a8bd-977c9e9765e61656.elb.us-east-1.amazonaws.com/api/redoc
```

---

## Using with Portal/CLI

### Portal Configuration
Update your portal `.env` file:
```env
NEXT_PUBLIC_API_URL=http://a5778e36f7e224c0fa8564d322f5a8bd-977c9e9765e61656.elb.us-east-1.amazonaws.com
```

### CLI Configuration
```bash
cd cli
npm run dev -- config set apiUrl http://a5778e36f7e224c0fa8564d322f5a8bd-977c9e9765e61656.elb.us-east-1.amazonaws.com
```

---

## Load Balancer Details

**Type**: Network Load Balancer (NLB)
**Scheme**: Internet-facing
**DNS**: a5778e36f7e224c0fa8564d322f5a8bd-977c9e9765e61656.elb.us-east-1.amazonaws.com
**Port**: 80 (HTTP)
**Health Check**: TCP on port 80
**Targets**: 2 healthy pods in EKS

---

## Security Notes

⚠️ **Current Setup**:
- HTTP only (no HTTPS/SSL)
- No authentication required (Okta disabled)
- Public internet access
- Suitable for hackathon/development

🔒 **For Production**:
- Add HTTPS with ACM certificate
- Enable Okta authentication
- Add API rate limiting
- Configure WAF rules
- Restrict access by IP if needed

---

## Monitoring

### Check API Status
```bash
# Health check
curl http://a5778e36f7e224c0fa8564d322f5a8bd-977c9e9765e61656.elb.us-east-1.amazonaws.com/health

# Metrics
curl http://a5778e36f7e224c0fa8564d322f5a8bd-977c9e9765e61656.elb.us-east-1.amazonaws.com/metrics
```

### Check Kubernetes Pods
```bash
kubectl get pods -n forge-api
kubectl logs -n forge-api -l app=forge-api --tail=50
```

### Check Load Balancer
```bash
aws elbv2 describe-load-balancers --region us-east-1 \
  --query 'LoadBalancers[?contains(DNSName, `a5778e36f7e224c0fa8564d322f5a8bd`)]'
```

---

## Troubleshooting

### API Not Responding
```bash
# Check pods
kubectl get pods -n forge-api

# Check service
kubectl get svc -n forge-api

# Check load balancer health
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --load-balancer-arn $(aws elbv2 describe-load-balancers \
      --region us-east-1 \
      --query 'LoadBalancers[?contains(DNSName, `a5778e36f7e224c0fa8564d322f5a8bd`)].LoadBalancerArn' \
      --output text) \
    --region us-east-1 \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text) \
  --region us-east-1
```

### Slow Response
- Check pod logs for errors
- Verify database connectivity
- Check EKS node resources

---

## Next Steps

1. ✅ API is publicly accessible
2. Configure portal to use this API URL
3. Build and configure CLI
4. Test WorkSpace provisioning
5. (Optional) Add custom domain
6. (Optional) Enable HTTPS
7. (Optional) Enable authentication

---

## Success! 🎉

Your RobCo Forge API is now **live and accessible** from anywhere on the internet!

You can start building your portal, configuring your CLI, or testing the API directly.

**API URL**: http://a5778e36f7e224c0fa8564d322f5a8bd-977c9e9765e61656.elb.us-east-1.amazonaws.com

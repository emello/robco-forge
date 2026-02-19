# Getting Started with RobCo Forge

## Quick Start (5 minutes)

### 1. Prerequisites
```bash
# Install required tools
- Python 3.11+
- Node.js 18+
- Docker Desktop
```

### 2. Clone and Start
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Start local development environment
./scripts/dev-start.sh
```

This will:
- Start PostgreSQL and Redis in Docker
- Set up Python virtual environment
- Install all dependencies
- Run database migrations
- Start the API server on http://localhost:8000

### 3. Test the API
```bash
# Check API health
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs
```

### 4. Use the CLI
```bash
cd cli

# Configure CLI
npm run dev -- config set apiUrl http://localhost:8000

# Test commands (note: requires authentication)
npm run dev -- --help
npm run dev -- config list
```

## What's Been Built

### ✅ Backend API (Python/FastAPI)
- **Workspace Management**: Provision, start, stop, terminate workspaces
- **Cost Tracking**: Real-time cost calculation and aggregation
- **Budget Enforcement**: Automatic budget checks and warnings
- **Lucy AI**: Conversational interface with intent recognition
- **Authentication**: Okta SSO integration with JWT tokens
- **Audit Logging**: Comprehensive audit trail

**Location**: `api/`
**Start**: `cd api && uvicorn src.main:app --reload`
**Docs**: http://localhost:8000/docs

### ✅ CLI (TypeScript)
- **Workspace Commands**: launch, list, start, stop, terminate, describe
- **Cost Commands**: summary, recommendations, budget
- **Lucy Integration**: Ask Lucy questions via CLI
- **Configuration**: Manage CLI settings

**Location**: `cli/`
**Start**: `cd cli && npm run dev -- <command>`
**Help**: `npm run dev -- --help`

### ✅ Infrastructure (Terraform + CDK)
- **Terraform**: VPC, EKS, RDS, FSx, WorkSpaces directory
- **CDK**: Kubernetes deployments, services, ingress
- **Secrets**: External Secrets Operator integration

**Location**: `terraform/` and `cdk/`

## Development Workflow

### Running the API
```bash
cd api

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run specific test
pytest tests/test_intent_recognizer.py -v
```

### Running the CLI
```bash
cd cli

# Development mode
npm run dev -- <command>

# Build
npm run build

# Run built version
node dist/index.js <command>

# Link globally (optional)
npm link
forge <command>
```

### Database Migrations
```bash
cd api
source venv/bin/activate

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Check current version
alembic current
```

## Project Structure

```
robco-forge/
├── api/                    # Python FastAPI backend
│   ├── src/
│   │   ├── api/           # API routes
│   │   ├── auth/          # Authentication
│   │   ├── cost/          # Cost engine
│   │   ├── lucy/          # Lucy AI service
│   │   ├── models/        # Database models
│   │   └── provisioning/  # Workspace provisioning
│   ├── tests/             # API tests
│   └── alembic/           # Database migrations
│
├── cli/                    # TypeScript CLI
│   ├── src/
│   │   ├── commands/      # CLI commands
│   │   ├── api/           # API client
│   │   ├── config/        # Configuration
│   │   └── utils/         # Utilities
│   └── dist/              # Built output
│
├── terraform/              # Infrastructure as Code
│   ├── modules/           # Reusable modules
│   └── environments/      # Environment configs
│
├── cdk/                    # Kubernetes deployments
│   ├── lib/               # CDK stacks
│   └── k8s-manifests/     # Kubernetes YAML
│
├── docs/                   # Documentation
├── scripts/                # Utility scripts
└── .kiro/specs/           # Feature specifications
```

## Common Tasks

### Add a New API Endpoint
```bash
cd api/src/api

# 1. Create route file (e.g., new_feature_routes.py)
# 2. Define endpoints with FastAPI decorators
# 3. Add to main.py:
#    from .api.new_feature_routes import router as new_feature_router
#    app.include_router(new_feature_router)
# 4. Write tests in tests/test_new_feature.py
# 5. Run tests: pytest tests/test_new_feature.py
```

### Add a New CLI Command
```bash
cd cli/src/commands

# 1. Create command file (e.g., new-command.ts)
# 2. Export createNewCommand() function
# 3. Add to index.ts:
#    import { createNewCommand } from './commands/new-command';
#    program.addCommand(createNewCommand());
# 4. Build: npm run build
# 5. Test: npm run dev -- new-command --help
```

### Add a New Database Model
```bash
cd api/src/models

# 1. Create model file (e.g., new_model.py)
# 2. Define SQLAlchemy model
# 3. Import in models/__init__.py
# 4. Create migration:
#    alembic revision --autogenerate -m "Add new_model"
# 5. Review migration in alembic/versions/
# 6. Apply: alembic upgrade head
```

## Testing

### API Tests
```bash
cd api

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_lucy_audit.py -v

# Run specific test
pytest tests/test_lucy_audit.py::TestLucyAuditLogger::test_log_tool_execution_success -v
```

### CLI Tests
```bash
cd cli

# Run tests (when implemented)
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test -- workspace.test.ts
```

## Environment Variables

### API (.env)
```bash
# Required
DATABASE_URL=postgresql://forge:forge_dev_password@localhost:5432/forge
REDIS_URL=redis://localhost:6379/0

# Optional for local dev
OKTA_DOMAIN=your-domain.okta.com
OKTA_CLIENT_ID=your-client-id
OKTA_CLIENT_SECRET=your-client-secret
JWT_SECRET_KEY=dev-secret-key-change-in-production
ANTHROPIC_API_KEY=your-anthropic-key
AWS_REGION=us-east-1
```

### CLI (.env)
```bash
FORGE_API_URL=http://localhost:8000
FORGE_DEFAULT_BUNDLE=PERFORMANCE
FORGE_DEFAULT_OS=Linux
FORGE_OUTPUT_FORMAT=table
```

## Troubleshooting

### API won't start
```bash
# Check if port 8000 is in use
lsof -i :8000
kill -9 <PID>

# Check database connection
docker ps | grep postgres
docker logs forge-postgres

# Reinstall dependencies
cd api
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database issues
```bash
# Reset database
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d

# Wait for PostgreSQL
sleep 5

# Run migrations
cd api
source venv/bin/activate
alembic upgrade head
```

### CLI build issues
```bash
# Clean and rebuild
cd cli
rm -rf node_modules dist
npm install
npm run build
```

## Next Steps

1. **Explore the API**: http://localhost:8000/docs
2. **Try CLI commands**: `cd cli && npm run dev -- --help`
3. **Read the specs**: `.kiro/specs/robco-forge/`
4. **Check deployment guide**: `DEPLOYMENT_GUIDE.md`
5. **Review architecture**: `docs/`

## Resources

- **API Documentation**: `api/README.md`
- **CLI Documentation**: `cli/README.md`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Infrastructure Validation**: `docs/infrastructure-validation-checklist.md`
- **Lucy Validation**: `api/LUCY_VALIDATION_CHECKPOINT.md`

## Getting Help

- Check existing documentation in `docs/`
- Review test files for usage examples
- Check API docs at http://localhost:8000/docs
- Review the spec files in `.kiro/specs/robco-forge/`

## Stop Development Environment

```bash
# Stop all services
./scripts/dev-stop.sh

# Or manually:
pkill -f "uvicorn src.main:app"
docker-compose -f docker-compose.dev.yml down
```

---

**Ready to deploy?** See `DEPLOYMENT_GUIDE.md` for production deployment instructions.

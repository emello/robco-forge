# RobCo Forge API Service

FastAPI-based backend service for the RobCo Forge platform.

## Database Setup

### Prerequisites

- PostgreSQL 15+
- Python 3.11+

### Environment Variables

```bash
export DATABASE_URL="postgresql://forge:forge@localhost:5432/forge"
```

### Initial Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize Alembic (if not already done):
```bash
cd api
alembic init alembic  # Already done, skip this
```

3. Run migrations:
```bash
alembic upgrade head
```

### Database Models

The following models are implemented:

- **WorkSpace**: AWS WorkSpaces instances with lifecycle management
- **Blueprint**: Version-controlled environment templates
- **CostRecord**: Real-time cost tracking with aggregation support
- **UserBudget**: Budget tracking with 80% warning and 100% hard limit
- **AuditLog**: Tamper-evident audit logging with monthly partitioning

### Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback one migration:
```bash
alembic downgrade -1
```

### Audit Log Partitioning

Audit logs are partitioned by month for efficient querying and archival (Requirement 10.3).

To create partitions for upcoming months:
```bash
python scripts/create_audit_log_partition.py 3  # Create 3 months ahead
```

This should be run monthly via cron or scheduled task.

### Performance Indexes

The following indexes are created for optimal query performance:

**WorkSpaces:**
- `user_id` - for user workspace queries
- `team_id` - for team workspace queries

**Cost Records:**
- `workspace_id`, `user_id`, `team_id` - for cost aggregation
- `period_start`, `period_end`, `recorded_at` - for time-based queries
- Composite indexes for efficient aggregation by user/team/workspace + period

**Audit Logs:**
- `timestamp` - for time-based queries
- `user_id` - for user activity queries
- `action_type` - for action-based queries
- `resource_id` - for resource-based queries
- Composite indexes for efficient filtering

**Blueprints:**
- `team_id` - for team-scoped blueprint access

**User Budgets:**
- `scope_id` - for budget lookups

## Requirements Traceability

- **Requirement 1.1**: WorkSpace model with provisioning fields
- **Requirement 1.7**: Idle timeout enforcement via `auto_stop_timeout_minutes`
- **Requirement 1.9**: Maximum lifetime enforcement via `max_lifetime_days`
- **Requirement 2.1**: Blueprint model with version control
- **Requirement 2.3**: Blueprint version immutability (new versions preserve old)
- **Requirement 10.1**: Comprehensive audit logging
- **Requirement 10.2**: Audit log fields (timestamp, user, action, resource, result, IP)
- **Requirement 10.3**: Tamper-evident storage, partitioning, 7-year retention
- **Requirement 11.1**: Real-time cost tracking per WorkSpace
- **Requirement 12.1**: Budget configuration per user/team/project
- **Requirement 12.2**: Warning at 80% threshold
- **Requirement 12.3**: Hard limit at 100% threshold

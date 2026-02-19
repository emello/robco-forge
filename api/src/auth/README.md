# Authentication and Authorization Module

This module implements Okta SSO integration with SAML 2.0 and a comprehensive RBAC (Role-Based Access Control) system for the RobCo Forge platform.

## Overview

The authentication and authorization system provides:

1. **Okta SSO Integration** - SAML 2.0 authentication with MFA requirement
2. **JWT Token Management** - Secure token generation and validation
3. **RBAC System** - Role-based permissions with four role levels
4. **Time-Bound Credentials** - Support for contractor credential expiration
5. **Bundle Type Restrictions** - Role-based access to WorkSpace bundle types

## Requirements Validation

This implementation validates the following requirements:

- **Requirement 8.1**: SSO authentication via Okta using SAML 2.0
- **Requirement 8.2**: Multi-factor authentication requirement
- **Requirement 8.3**: RBAC implementation for all resources and actions
- **Requirement 8.4**: Permission checking middleware
- **Requirement 8.5**: Time-bound credentials for contractors
- **Requirement 8.6**: Bundle type restrictions for contractors

## Architecture

### Components

1. **OktaSSOHandler** (`okta_sso.py`)
   - Handles SAML 2.0 authentication flow
   - Initiates SSO login with Okta
   - Processes SAML callbacks
   - Verifies MFA completion
   - Manages SSO logout

2. **JWTManager** (`jwt_manager.py`)
   - Generates JWT access and refresh tokens
   - Validates token signatures and expiration
   - Supports custom expiry for contractor credentials
   - Handles token refresh

3. **RBACManager** (`rbac.py`)
   - Defines role hierarchy and permissions
   - Checks user permissions
   - Validates bundle type access
   - Enforces time-bound credentials

4. **User Model** (`../models/user.py`)
   - Stores user authentication data
   - Tracks roles and team membership
   - Manages contractor credential expiry

5. **Auth Routes** (`../api/auth_routes.py`)
   - Provides authentication API endpoints
   - Implements role assignment API
   - Exposes current user information

## Role Hierarchy

The system defines four roles with increasing privilege levels:

### 1. Contractor (Least Privileged)
- **Time-bound credentials**: Credentials expire after configured period
- **Limited WorkSpace permissions**: Create, read, start, stop, connect
- **Read-only Blueprint access**
- **Own cost visibility only**
- **Restricted bundle types**: Standard and Performance only

### 2. Engineer (Standard User)
- **Full WorkSpace permissions**: Create, read, update, delete, start, stop, connect
- **Blueprint management**: Create, read, update
- **Team cost visibility**: Own and team costs
- **Most bundle types**: All except GraphicsPro

### 3. Team Lead (Team Manager)
- **All engineer permissions**
- **Full Blueprint management**: Including publish
- **Team cost management**: Export reports, update budgets
- **User management**: Read and update team members
- **Audit log access**
- **All bundle types**: Including GraphicsPro

### 4. Admin (Full Access)
- **Full system access**
- **All permissions**
- **User role assignment**
- **Budget override capability**
- **Global cost visibility**

## Permissions

The system defines granular permissions across resource types:

### WorkSpace Permissions
- `workspace:create` - Create new WorkSpaces
- `workspace:read` - View WorkSpace details
- `workspace:update` - Modify WorkSpace configuration
- `workspace:delete` - Terminate WorkSpaces
- `workspace:start` - Start stopped WorkSpaces
- `workspace:stop` - Stop running WorkSpaces
- `workspace:connect` - Connect to WorkSpaces

### Blueprint Permissions
- `blueprint:create` - Create new Blueprints
- `blueprint:read` - View Blueprint details
- `blueprint:update` - Modify Blueprints
- `blueprint:delete` - Delete Blueprints
- `blueprint:publish` - Publish Blueprints to team

### Cost Permissions
- `cost:read:own` - View own costs
- `cost:read:team` - View team costs
- `cost:read:all` - View all costs (admin)
- `cost:export` - Export cost reports

### Budget Permissions
- `budget:read` - View budget information
- `budget:update` - Update budget limits
- `budget:override` - Override budget restrictions

### User Management Permissions
- `user:read` - View user information
- `user:update` - Update user details
- `user:delete` - Delete users
- `user:assign_role` - Assign roles to users

### Bundle Type Permissions
- `bundle:standard` - Access Standard bundle
- `bundle:performance` - Access Performance bundle
- `bundle:power` - Access Power bundle
- `bundle:powerpro` - Access PowerPro bundle
- `bundle:graphics` - Access Graphics.g4dn bundle
- `bundle:graphicspro` - Access GraphicsPro.g4dn bundle

## Authentication Flow

### SSO Login Flow

```
1. User → POST /api/v1/auth/login
2. API → Generate SAML AuthnRequest
3. API → Return redirect URL to Okta
4. User → Redirect to Okta login page
5. User → Authenticate with Okta (username + password + MFA)
6. Okta → POST SAML Response to /api/v1/auth/callback
7. API → Validate SAML Response
8. API → Verify MFA completion
9. API → Create/update user in database
10. API → Generate JWT access and refresh tokens
11. API → Return tokens to user
```

### Token Validation Flow

```
1. User → API request with Authorization: Bearer <token>
2. API → Extract token from header
3. API → Validate token signature and expiration
4. API → Check user exists and is active
5. API → Check contractor credential expiry (if applicable)
6. API → Extract user data from token
7. API → Proceed with request
```

### Permission Check Flow

```
1. API → Extract user roles from token
2. API → Get permissions for roles
3. API → Check if required permission exists
4. API → Check credential expiry (for contractors)
5. API → Allow or deny request
```

## API Endpoints

### POST /api/v1/auth/login
Initiate SSO login with Okta.

**Request:**
```json
{
  "relay_state": "optional-state-to-preserve"
}
```

**Response:**
```json
{
  "redirect_url": "https://your-okta-domain.okta.com/...",
  "message": "Redirect to Okta SSO login"
}
```

### POST /api/v1/auth/callback
Handle SSO callback from Okta (receives SAML response).

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "user@robco.com",
    "email": "user@robco.com",
    "name": "John Doe",
    "roles": ["engineer"],
    "is_contractor": false
  }
}
```

### POST /api/v1/auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer"
}
```

### POST /api/v1/auth/logout
Logout user and initiate SSO logout.

**Response:**
```json
{
  "redirect_url": "https://your-okta-domain.okta.com/logout"
}
```

### POST /api/v1/auth/roles/assign
Assign roles to a user (admin only).

**Request:**
```json
{
  "user_id": "user@robco.com",
  "roles": ["engineer", "team_lead"],
  "credential_expiry": "2026-12-31T23:59:59Z"  // Optional, for contractors
}
```

**Response:**
```json
{
  "user_id": "user@robco.com",
  "roles": ["engineer", "team_lead"],
  "is_contractor": false,
  "credential_expiry": null,
  "message": "Roles successfully assigned to user user@robco.com"
}
```

### GET /api/v1/auth/me
Get current user information.

**Response:**
```json
{
  "user_id": "user@robco.com",
  "email": "user@robco.com",
  "name": "John Doe",
  "roles": ["engineer"],
  "is_contractor": false,
  "credential_expiry": null,
  "permissions": ["workspace:create", "workspace:read", ...],
  "allowed_bundle_types": ["STANDARD", "PERFORMANCE", "POWER", ...],
  "last_login": "2026-02-18T14:30:00Z"
}
```

## Usage Examples

### Protecting API Endpoints

```python
from fastapi import APIRouter, Depends
from ..auth import Permission
from ..api.auth_routes import require_permission, get_current_user

router = APIRouter()

# Require specific permission
@router.post("/workspaces")
async def create_workspace(
    current_user = Depends(require_permission(Permission.WORKSPACE_CREATE))
):
    # User has workspace:create permission
    pass

# Just require authentication
@router.get("/workspaces")
async def list_workspaces(
    current_user = Depends(get_current_user)
):
    # User is authenticated
    pass
```

### Checking Permissions Programmatically

```python
from ..auth import RBACManager, Permission

rbac = RBACManager()

# Check if user has permission
has_perm = rbac.has_permission(
    user_roles=["engineer"],
    required_permission=Permission.WORKSPACE_CREATE
)

# Check bundle access
can_use_graphics = rbac.check_bundle_access(
    user_roles=["contractor"],
    bundle_type="GRAPHICS_G4DN"
)  # Returns False for contractors

# Get allowed bundle types
allowed_bundles = rbac.get_allowed_bundle_types(
    user_roles=["contractor"]
)  # Returns ["STANDARD", "PERFORMANCE"]
```

### Contractor Time-Bound Credentials

```python
from datetime import datetime, timedelta
from ..auth import JWTManager

jwt_manager = JWTManager(secret_key="your-secret")

# Generate token with custom expiry for contractor
contractor_expiry = datetime.utcnow() + timedelta(days=90)
token = jwt_manager.generate_token(
    user_id="contractor@external.com",
    email="contractor@external.com",
    roles=["contractor"],
    custom_expiry=contractor_expiry
)

# Token will expire after 90 days
```

## Configuration

Required environment variables:

```bash
# Okta SSO
OKTA_METADATA_URL=https://your-okta-domain.okta.com/app/your-app-id/sso/saml/metadata
OKTA_SP_ENTITY_ID=https://forge.robco.com
OKTA_SP_ACS_URL=https://forge.robco.com/api/v1/auth/callback
OKTA_SP_SLS_URL=https://forge.robco.com/api/v1/auth/logout

# JWT
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Security Considerations

1. **MFA Enforcement**: All authentication requires MFA completion verified via SAML AuthnContext
2. **Token Security**: JWT tokens signed with HS256, stored securely on client
3. **Credential Expiry**: Contractor credentials automatically expire after configured period
4. **Permission Checks**: All API endpoints protected with permission middleware
5. **Audit Logging**: All authentication events logged for compliance
6. **HTTPS Only**: All authentication endpoints require HTTPS in production

## Testing

The authentication system should be tested with:

1. **Unit tests** for individual components (JWT, RBAC, SAML)
2. **Integration tests** for authentication flow
3. **Property-based tests** for RBAC enforcement (see tasks 5.3, 5.4)

## Database Schema

### users table

```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    roles JSON NOT NULL,
    team_id VARCHAR,
    is_contractor BOOLEAN,
    credential_expiry TIMESTAMP,
    last_login TIMESTAMP,
    mfa_verified BOOLEAN,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,
    is_active BOOLEAN
);

CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_team_id ON users(team_id);
CREATE INDEX ix_users_is_contractor ON users(is_contractor);
CREATE INDEX ix_users_is_active ON users(is_active);
```

## Migration

Run Alembic migration to create users table:

```bash
cd api
alembic upgrade head
```

## Dependencies

- `python3-saml==1.16.0` - SAML 2.0 authentication
- `PyJWT==2.8.0` - JWT token management
- `fastapi` - API framework
- `sqlalchemy` - ORM for user model
- `pydantic` - Request/response validation

## Future Enhancements

1. **OAuth 2.0 Support**: Add OAuth 2.0 as alternative to SAML
2. **API Key Authentication**: Support API keys for CLI/automation
3. **Session Management**: Track active sessions per user
4. **Password Policies**: Enforce password complexity for local accounts
5. **Audit Trail**: Enhanced audit logging for all authentication events

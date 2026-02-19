"""Authentication API routes."""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..auth import OktaSSOHandler, JWTManager, RBACManager, Role, Permission
from ..auth.rbac import PermissionDeniedError
from ..database import get_db
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


# Request/Response models
class LoginInitiateResponse(BaseModel):
    """Response for SSO login initiation."""
    redirect_url: str
    message: str = "Redirect to Okta SSO login"


class LoginCallbackResponse(BaseModel):
    """Response for SSO callback."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: Dict[str, Any]


class RoleAssignmentRequest(BaseModel):
    """Request to assign roles to a user."""
    user_id: str
    roles: list[str]
    credential_expiry: Optional[datetime] = None  # For contractors


class RoleAssignmentResponse(BaseModel):
    """Response for role assignment."""
    user_id: str
    roles: list[str]
    is_contractor: bool
    credential_expiry: Optional[datetime] = None
    message: str


# Dependency injection
def get_okta_sso_handler() -> OktaSSOHandler:
    """Get Okta SSO handler instance."""
    # In production, these would come from environment variables or config
    from ..config import settings
    
    jwt_manager = get_jwt_manager()
    
    return OktaSSOHandler(
        okta_metadata_url=settings.OKTA_METADATA_URL,
        sp_entity_id=settings.OKTA_SP_ENTITY_ID,
        sp_acs_url=settings.OKTA_SP_ACS_URL,
        sp_sls_url=settings.OKTA_SP_SLS_URL,
        jwt_manager=jwt_manager,
    )


def get_jwt_manager() -> JWTManager:
    """Get JWT manager instance."""
    from ..config import settings
    
    return JWTManager(
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        access_token_expire_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    )


def get_rbac_manager() -> RBACManager:
    """Get RBAC manager instance."""
    return RBACManager()


def get_current_user(
    request: Request,
    jwt_manager: JWTManager = Depends(get_jwt_manager),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Extract and validate current user from JWT token.
    
    Args:
        request: FastAPI request object
        jwt_manager: JWT manager instance
        db: Database session
        
    Returns:
        User data from token
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Validate token and extract payload
        payload = jwt_manager.validate_token(token)
        
        # Check if user exists and is active
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        
        # Check contractor credential expiry
        if user.is_contractor and user.is_credentials_expired():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contractor credentials have expired",
            )
        
        return {
            "user_id": payload["sub"],
            "email": payload["email"],
            "roles": payload["roles"],
            "token_type": payload.get("type", "access"),
            "exp": payload.get("exp"),
        }
        
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_permission(required_permission: Permission):
    """Dependency to check if user has required permission.
    
    Args:
        required_permission: Permission to check
        
    Returns:
        Dependency function
    """
    def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
        rbac_manager: RBACManager = Depends(get_rbac_manager),
    ) -> Dict[str, Any]:
        """Check if current user has required permission."""
        user_roles = current_user.get("roles", [])
        credential_expiry = current_user.get("exp")
        
        if credential_expiry:
            credential_expiry = datetime.fromtimestamp(credential_expiry)
        
        has_perm = rbac_manager.has_permission(
            user_roles=user_roles,
            required_permission=required_permission,
            credential_expiry=credential_expiry,
        )
        
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {required_permission.value} required",
            )
        
        return current_user
    
    return permission_checker


# Routes
@router.post("/login", response_model=LoginInitiateResponse)
async def initiate_sso_login(
    request: Request,
    relay_state: Optional[str] = None,
    sso_handler: OktaSSOHandler = Depends(get_okta_sso_handler),
):
    """Initiate SSO login with Okta.
    
    Generates SAML AuthnRequest and redirects to Okta login page.
    
    Args:
        request: FastAPI request
        relay_state: Optional state to preserve after authentication
        sso_handler: Okta SSO handler
        
    Returns:
        Redirect URL to Okta SSO login
        
    Validates: Requirements 8.1
    """
    try:
        # Prepare request data for SAML
        request_data = {
            "https": request.url.scheme == "https",
            "http_host": request.url.hostname,
            "script_name": request.url.path,
            "server_port": request.url.port or (443 if request.url.scheme == "https" else 80),
            "get_data": dict(request.query_params),
            "post_data": {},
        }
        
        # Initiate SSO login
        redirect_url = sso_handler.initiate_login(request_data, relay_state)
        
        return LoginInitiateResponse(redirect_url=redirect_url)
        
    except Exception as e:
        logger.error(f"Failed to initiate SSO login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate SSO login: {e}",
        )


@router.post("/callback", response_model=LoginCallbackResponse)
async def handle_sso_callback(
    request: Request,
    db: Session = Depends(get_db),
    sso_handler: OktaSSOHandler = Depends(get_okta_sso_handler),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
):
    """Handle SSO callback from Okta after authentication.
    
    Processes SAML response, validates MFA, and generates JWT tokens.
    
    Args:
        request: FastAPI request with SAML response
        db: Database session
        sso_handler: Okta SSO handler
        jwt_manager: JWT manager
        
    Returns:
        Access and refresh tokens with user data
        
    Validates: Requirements 8.1, 8.2
    """
    try:
        # Get form data (SAML response)
        form_data = await request.form()
        
        # Prepare request data for SAML
        request_data = {
            "https": request.url.scheme == "https",
            "http_host": request.url.hostname,
            "script_name": request.url.path,
            "server_port": request.url.port or (443 if request.url.scheme == "https" else 80),
            "get_data": dict(request.query_params),
            "post_data": dict(form_data),
        }
        
        # Handle SAML callback
        user_data = sso_handler.handle_callback(request_data)
        
        # Create or update user in database
        user = db.query(User).filter(User.id == user_data["user_id"]).first()
        
        if not user:
            # Create new user
            user = User(
                id=user_data["user_id"],
                email=user_data["email"],
                name=user_data["name"],
                roles=user_data["roles"],
                mfa_verified=user_data["mfa_verified"],
                last_login=datetime.utcnow(),
            )
            db.add(user)
        else:
            # Update existing user
            user.last_login = datetime.utcnow()
            user.mfa_verified = user_data["mfa_verified"]
            user.roles = user_data["roles"]
        
        db.commit()
        db.refresh(user)
        
        # Generate refresh token
        refresh_token = jwt_manager.generate_token(
            user_id=user.id,
            email=user.email,
            roles=user.roles,
            token_type="refresh",
            custom_expiry=user.credential_expiry if user.is_contractor else None,
        )
        
        return LoginCallbackResponse(
            access_token=user_data["jwt_token"],
            refresh_token=refresh_token,
            expires_in=jwt_manager.access_token_expire_minutes * 60,
            user={
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "roles": user.roles,
                "is_contractor": user.is_contractor,
            },
        )
        
    except Exception as e:
        logger.error(f"Failed to handle SSO callback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {e}",
        )


@router.post("/refresh", response_model=Dict[str, str])
async def refresh_access_token(
    refresh_token: str,
    jwt_manager: JWTManager = Depends(get_jwt_manager),
):
    """Refresh access token using refresh token.
    
    Args:
        refresh_token: Valid refresh token
        jwt_manager: JWT manager
        
    Returns:
        New access token
    """
    try:
        new_access_token = jwt_manager.refresh_token(refresh_token)
        
        return {
            "access_token": new_access_token,
            "token_type": "Bearer",
        }
        
    except Exception as e:
        logger.error(f"Failed to refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to refresh token: {e}",
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    sso_handler: OktaSSOHandler = Depends(get_okta_sso_handler),
):
    """Logout user and initiate SSO logout.
    
    Args:
        request: FastAPI request
        current_user: Current authenticated user
        sso_handler: Okta SSO handler
        
    Returns:
        Redirect URL to Okta logout
    """
    try:
        # Prepare request data
        request_data = {
            "https": request.url.scheme == "https",
            "http_host": request.url.hostname,
            "script_name": request.url.path,
            "server_port": request.url.port or (443 if request.url.scheme == "https" else 80),
            "get_data": dict(request.query_params),
            "post_data": {},
        }
        
        # Initiate SSO logout
        logout_url = sso_handler.logout(
            request_data=request_data,
            name_id=current_user["user_id"],
        )
        
        return {"redirect_url": logout_url}
        
    except Exception as e:
        logger.error(f"Failed to logout: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to logout: {e}",
        )


@router.post("/roles/assign", response_model=RoleAssignmentResponse)
async def assign_roles(
    assignment: RoleAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.USER_ASSIGN_ROLE)),
):
    """Assign roles to a user.
    
    Only admins can assign roles. Supports time-bound credentials for contractors.
    
    Args:
        assignment: Role assignment request
        db: Database session
        current_user: Current authenticated user (must have USER_ASSIGN_ROLE permission)
        
    Returns:
        Updated user role information
        
    Validates: Requirements 8.3, 8.5
    """
    try:
        # Validate roles
        valid_roles = [role.value for role in Role]
        invalid_roles = [r for r in assignment.roles if r not in valid_roles]
        
        if invalid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid roles: {invalid_roles}",
            )
        
        # Get user
        user = db.query(User).filter(User.id == assignment.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {assignment.user_id}",
            )
        
        # Update roles
        user.roles = assignment.roles
        user.is_contractor = Role.CONTRACTOR.value in assignment.roles
        
        # Set credential expiry for contractors
        if user.is_contractor and assignment.credential_expiry:
            user.credential_expiry = assignment.credential_expiry
        elif not user.is_contractor:
            user.credential_expiry = None
        
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        logger.info(
            f"Roles assigned to user {user.id}",
            extra={
                "user_id": user.id,
                "roles": user.roles,
                "assigned_by": current_user["user_id"],
            }
        )
        
        return RoleAssignmentResponse(
            user_id=user.id,
            roles=user.roles,
            is_contractor=user.is_contractor,
            credential_expiry=user.credential_expiry,
            message=f"Roles successfully assigned to user {user.id}",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign roles: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign roles: {e}",
        )


@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
    rbac_manager: RBACManager = Depends(get_rbac_manager),
):
    """Get current user information including permissions.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        rbac_manager: RBAC manager
        
    Returns:
        User information with roles and permissions
    """
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Get user permissions
    permissions = rbac_manager.get_permissions_for_roles(user.roles)
    allowed_bundles = rbac_manager.get_allowed_bundle_types(user.roles)
    
    return {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "roles": user.roles,
        "is_contractor": user.is_contractor,
        "credential_expiry": user.credential_expiry.isoformat() if user.credential_expiry else None,
        "permissions": [p.value for p in permissions],
        "allowed_bundle_types": allowed_bundles,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }

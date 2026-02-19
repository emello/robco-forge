"""Role-Based Access Control (RBAC) system."""

from typing import List, Optional, Set, Dict, Any
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """System permissions for RBAC.
    
    Requirements:
    - 8.3: RBAC for all resources and actions
    - 8.4: Permission checking for all actions
    """
    
    # WorkSpace permissions
    WORKSPACE_CREATE = "workspace:create"
    WORKSPACE_READ = "workspace:read"
    WORKSPACE_UPDATE = "workspace:update"
    WORKSPACE_DELETE = "workspace:delete"
    WORKSPACE_START = "workspace:start"
    WORKSPACE_STOP = "workspace:stop"
    WORKSPACE_CONNECT = "workspace:connect"
    
    # Blueprint permissions
    BLUEPRINT_CREATE = "blueprint:create"
    BLUEPRINT_READ = "blueprint:read"
    BLUEPRINT_UPDATE = "blueprint:update"
    BLUEPRINT_DELETE = "blueprint:delete"
    BLUEPRINT_PUBLISH = "blueprint:publish"
    
    # Cost permissions
    COST_READ_OWN = "cost:read:own"
    COST_READ_TEAM = "cost:read:team"
    COST_READ_ALL = "cost:read:all"
    COST_EXPORT = "cost:export"
    
    # Budget permissions
    BUDGET_READ = "budget:read"
    BUDGET_UPDATE = "budget:update"
    BUDGET_OVERRIDE = "budget:override"
    
    # User management permissions
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_ASSIGN_ROLE = "user:assign_role"
    
    # Audit log permissions
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"
    
    # Bundle type permissions (for contractors)
    BUNDLE_STANDARD = "bundle:standard"
    BUNDLE_PERFORMANCE = "bundle:performance"
    BUNDLE_POWER = "bundle:power"
    BUNDLE_POWERPRO = "bundle:powerpro"
    BUNDLE_GRAPHICS = "bundle:graphics"
    BUNDLE_GRAPHICSPRO = "bundle:graphicspro"
    
    # Admin permissions
    ADMIN_FULL = "admin:full"


class Role(str, Enum):
    """User roles in the system.
    
    Role hierarchy (from least to most privileged):
    - CONTRACTOR: Limited access, time-bound credentials, restricted bundle types
    - ENGINEER: Standard engineer access
    - TEAM_LEAD: Team management and budget oversight
    - ADMIN: Full system access
    
    Requirements:
    - 8.3: Define role hierarchy
    - 8.5: Time-bound credentials for contractors
    - 8.6: Bundle type restrictions for contractors
    """
    
    CONTRACTOR = "contractor"
    ENGINEER = "engineer"
    TEAM_LEAD = "team_lead"
    ADMIN = "admin"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.CONTRACTOR: {
        # Limited WorkSpace permissions
        Permission.WORKSPACE_CREATE,
        Permission.WORKSPACE_READ,
        Permission.WORKSPACE_START,
        Permission.WORKSPACE_STOP,
        Permission.WORKSPACE_CONNECT,
        
        # Read-only Blueprint access
        Permission.BLUEPRINT_READ,
        
        # Own cost visibility only
        Permission.COST_READ_OWN,
        Permission.BUDGET_READ,
        
        # Limited bundle types (Standard and Performance only)
        Permission.BUNDLE_STANDARD,
        Permission.BUNDLE_PERFORMANCE,
    },
    
    Role.ENGINEER: {
        # Full WorkSpace permissions
        Permission.WORKSPACE_CREATE,
        Permission.WORKSPACE_READ,
        Permission.WORKSPACE_UPDATE,
        Permission.WORKSPACE_DELETE,
        Permission.WORKSPACE_START,
        Permission.WORKSPACE_STOP,
        Permission.WORKSPACE_CONNECT,
        
        # Blueprint permissions
        Permission.BLUEPRINT_CREATE,
        Permission.BLUEPRINT_READ,
        Permission.BLUEPRINT_UPDATE,
        
        # Cost visibility (own and team)
        Permission.COST_READ_OWN,
        Permission.COST_READ_TEAM,
        Permission.BUDGET_READ,
        
        # All bundle types except GraphicsPro
        Permission.BUNDLE_STANDARD,
        Permission.BUNDLE_PERFORMANCE,
        Permission.BUNDLE_POWER,
        Permission.BUNDLE_POWERPRO,
        Permission.BUNDLE_GRAPHICS,
    },
    
    Role.TEAM_LEAD: {
        # All engineer permissions
        Permission.WORKSPACE_CREATE,
        Permission.WORKSPACE_READ,
        Permission.WORKSPACE_UPDATE,
        Permission.WORKSPACE_DELETE,
        Permission.WORKSPACE_START,
        Permission.WORKSPACE_STOP,
        Permission.WORKSPACE_CONNECT,
        
        # Full Blueprint permissions
        Permission.BLUEPRINT_CREATE,
        Permission.BLUEPRINT_READ,
        Permission.BLUEPRINT_UPDATE,
        Permission.BLUEPRINT_DELETE,
        Permission.BLUEPRINT_PUBLISH,
        
        # Team cost visibility and management
        Permission.COST_READ_OWN,
        Permission.COST_READ_TEAM,
        Permission.COST_EXPORT,
        Permission.BUDGET_READ,
        Permission.BUDGET_UPDATE,
        
        # User management for team
        Permission.USER_READ,
        Permission.USER_UPDATE,
        
        # Audit log access
        Permission.AUDIT_READ,
        
        # All bundle types
        Permission.BUNDLE_STANDARD,
        Permission.BUNDLE_PERFORMANCE,
        Permission.BUNDLE_POWER,
        Permission.BUNDLE_POWERPRO,
        Permission.BUNDLE_GRAPHICS,
        Permission.BUNDLE_GRAPHICSPRO,
    },
    
    Role.ADMIN: {
        # Full system access
        Permission.ADMIN_FULL,
        
        # All permissions
        Permission.WORKSPACE_CREATE,
        Permission.WORKSPACE_READ,
        Permission.WORKSPACE_UPDATE,
        Permission.WORKSPACE_DELETE,
        Permission.WORKSPACE_START,
        Permission.WORKSPACE_STOP,
        Permission.WORKSPACE_CONNECT,
        
        Permission.BLUEPRINT_CREATE,
        Permission.BLUEPRINT_READ,
        Permission.BLUEPRINT_UPDATE,
        Permission.BLUEPRINT_DELETE,
        Permission.BLUEPRINT_PUBLISH,
        
        Permission.COST_READ_OWN,
        Permission.COST_READ_TEAM,
        Permission.COST_READ_ALL,
        Permission.COST_EXPORT,
        
        Permission.BUDGET_READ,
        Permission.BUDGET_UPDATE,
        Permission.BUDGET_OVERRIDE,
        
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_ASSIGN_ROLE,
        
        Permission.AUDIT_READ,
        Permission.AUDIT_EXPORT,
        
        Permission.BUNDLE_STANDARD,
        Permission.BUNDLE_PERFORMANCE,
        Permission.BUNDLE_POWER,
        Permission.BUNDLE_POWERPRO,
        Permission.BUNDLE_GRAPHICS,
        Permission.BUNDLE_GRAPHICSPRO,
    },
}


class RBACManager:
    """Manages role-based access control.
    
    Requirements:
    - 8.3: RBAC implementation
    - 8.4: Permission checking middleware
    - 8.5: Time-bound credentials for contractors
    - 8.6: Bundle type restrictions for contractors
    """
    
    def __init__(self):
        """Initialize RBAC manager."""
        self.role_permissions = ROLE_PERMISSIONS
    
    def get_permissions_for_role(self, role: Role) -> Set[Permission]:
        """Get all permissions for a given role.
        
        Args:
            role: User role
            
        Returns:
            Set of permissions for the role
        """
        return self.role_permissions.get(role, set())
    
    def get_permissions_for_roles(self, roles: List[str]) -> Set[Permission]:
        """Get combined permissions for multiple roles.
        
        Args:
            roles: List of role names
            
        Returns:
            Set of all permissions across all roles
        """
        all_permissions: Set[Permission] = set()
        
        for role_name in roles:
            try:
                role = Role(role_name)
                all_permissions.update(self.get_permissions_for_role(role))
            except ValueError:
                logger.warning(f"Unknown role: {role_name}")
                continue
        
        return all_permissions
    
    def has_permission(
        self,
        user_roles: List[str],
        required_permission: Permission,
        credential_expiry: Optional[datetime] = None,
    ) -> bool:
        """Check if user has required permission.
        
        Args:
            user_roles: List of user's role names
            required_permission: Permission to check
            credential_expiry: Optional credential expiry time (for contractors)
            
        Returns:
            True if user has permission, False otherwise
            
        Validates: Requirements 8.4, 8.5
        """
        # Check if credentials have expired (for contractors)
        if credential_expiry and datetime.utcnow() > credential_expiry:
            logger.warning(
                "Access denied: credentials expired",
                extra={"credential_expiry": credential_expiry.isoformat()}
            )
            return False
        
        # Get all permissions for user's roles
        user_permissions = self.get_permissions_for_roles(user_roles)
        
        # Admin has all permissions
        if Permission.ADMIN_FULL in user_permissions:
            return True
        
        # Check if user has the required permission
        has_perm = required_permission in user_permissions
        
        if not has_perm:
            logger.warning(
                f"Access denied: missing permission {required_permission.value}",
                extra={
                    "user_roles": user_roles,
                    "required_permission": required_permission.value,
                }
            )
        
        return has_perm
    
    def check_bundle_access(
        self,
        user_roles: List[str],
        bundle_type: str,
    ) -> bool:
        """Check if user can access a specific bundle type.
        
        Args:
            user_roles: List of user's role names
            bundle_type: Bundle type to check (e.g., "STANDARD", "GRAPHICS_G4DN")
            
        Returns:
            True if user can access the bundle type, False otherwise
            
        Validates: Requirements 8.6
        """
        # Map bundle types to permissions
        bundle_permission_map = {
            "STANDARD": Permission.BUNDLE_STANDARD,
            "PERFORMANCE": Permission.BUNDLE_PERFORMANCE,
            "POWER": Permission.BUNDLE_POWER,
            "POWERPRO": Permission.BUNDLE_POWERPRO,
            "GRAPHICS_G4DN": Permission.BUNDLE_GRAPHICS,
            "GRAPHICSPRO_G4DN": Permission.BUNDLE_GRAPHICSPRO,
        }
        
        required_permission = bundle_permission_map.get(bundle_type)
        if not required_permission:
            logger.warning(f"Unknown bundle type: {bundle_type}")
            return False
        
        return self.has_permission(user_roles, required_permission)
    
    def get_allowed_bundle_types(self, user_roles: List[str]) -> List[str]:
        """Get list of bundle types user can access.
        
        Args:
            user_roles: List of user's role names
            
        Returns:
            List of allowed bundle type names
            
        Validates: Requirements 8.6
        """
        user_permissions = self.get_permissions_for_roles(user_roles)
        
        bundle_types = []
        
        if Permission.BUNDLE_STANDARD in user_permissions:
            bundle_types.append("STANDARD")
        if Permission.BUNDLE_PERFORMANCE in user_permissions:
            bundle_types.append("PERFORMANCE")
        if Permission.BUNDLE_POWER in user_permissions:
            bundle_types.append("POWER")
        if Permission.BUNDLE_POWERPRO in user_permissions:
            bundle_types.append("POWERPRO")
        if Permission.BUNDLE_GRAPHICS in user_permissions:
            bundle_types.append("GRAPHICS_G4DN")
        if Permission.BUNDLE_GRAPHICSPRO in user_permissions:
            bundle_types.append("GRAPHICSPRO_G4DN")
        
        return bundle_types
    
    def is_contractor(self, user_roles: List[str]) -> bool:
        """Check if user is a contractor.
        
        Args:
            user_roles: List of user's role names
            
        Returns:
            True if user has contractor role, False otherwise
        """
        return Role.CONTRACTOR.value in user_roles
    
    def validate_resource_access(
        self,
        user_id: str,
        user_roles: List[str],
        resource_type: str,
        resource_owner_id: str,
        team_id: Optional[str] = None,
        required_permission: Optional[Permission] = None,
    ) -> bool:
        """Validate if user can access a specific resource.
        
        Args:
            user_id: User's ID
            user_roles: User's roles
            resource_type: Type of resource (workspace, blueprint, etc.)
            resource_owner_id: ID of resource owner
            team_id: Optional team ID for team-scoped resources
            required_permission: Optional specific permission to check
            
        Returns:
            True if user can access resource, False otherwise
        """
        user_permissions = self.get_permissions_for_roles(user_roles)
        
        # Admin can access everything
        if Permission.ADMIN_FULL in user_permissions:
            return True
        
        # Check specific permission if provided
        if required_permission and required_permission not in user_permissions:
            return False
        
        # Resource owner can always access their own resources
        if user_id == resource_owner_id:
            return True
        
        # Team leads can access team resources
        if Role.TEAM_LEAD.value in user_roles and team_id:
            # Would need to verify user is team lead of this specific team
            # This would require database lookup in real implementation
            return True
        
        return False


class RBACMiddleware:
    """Middleware for checking RBAC permissions on API requests.
    
    Requirements:
    - 8.4: Permission checking middleware
    """
    
    def __init__(self, rbac_manager: RBACManager):
        """Initialize RBAC middleware.
        
        Args:
            rbac_manager: RBAC manager instance
        """
        self.rbac_manager = rbac_manager
    
    def check_permission(
        self,
        user_data: Dict[str, Any],
        required_permission: Permission,
    ) -> bool:
        """Check if user has required permission.
        
        Args:
            user_data: User data from JWT token (user_id, roles, etc.)
            required_permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        user_roles = user_data.get("roles", [])
        credential_expiry = user_data.get("exp")
        
        if credential_expiry:
            credential_expiry = datetime.fromtimestamp(credential_expiry)
        
        return self.rbac_manager.has_permission(
            user_roles=user_roles,
            required_permission=required_permission,
            credential_expiry=credential_expiry,
        )


class PermissionDeniedError(Exception):
    """Raised when user lacks required permission."""
    
    def __init__(self, message: str, required_permission: Optional[Permission] = None):
        super().__init__(message)
        self.required_permission = required_permission

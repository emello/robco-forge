"""Basic tests for authentication and authorization system."""

import pytest
from datetime import datetime, timedelta

from src.auth import JWTManager, RBACManager, Role, Permission


class TestJWTManager:
    """Test JWT token generation and validation."""
    
    def test_generate_and_validate_token(self):
        """Test basic token generation and validation."""
        jwt_manager = JWTManager(secret_key="test-secret")
        
        # Generate token
        token = jwt_manager.generate_token(
            user_id="test@robco.com",
            email="test@robco.com",
            roles=["engineer"],
        )
        
        assert token is not None
        assert isinstance(token, str)
        
        # Validate token
        payload = jwt_manager.validate_token(token)
        
        assert payload["sub"] == "test@robco.com"
        assert payload["email"] == "test@robco.com"
        assert payload["roles"] == ["engineer"]
        assert payload["type"] == "access"
    
    def test_contractor_time_bound_credentials(self):
        """Test time-bound credentials for contractors."""
        jwt_manager = JWTManager(secret_key="test-secret")
        
        # Generate token with custom expiry (1 hour from now)
        custom_expiry = datetime.utcnow() + timedelta(hours=1)
        token = jwt_manager.generate_token(
            user_id="contractor@external.com",
            email="contractor@external.com",
            roles=["contractor"],
            custom_expiry=custom_expiry,
        )
        
        # Validate token
        payload = jwt_manager.validate_token(token)
        
        assert payload["sub"] == "contractor@external.com"
        assert payload["roles"] == ["contractor"]
        
        # Check expiry is close to custom expiry (within 60 seconds to account for timezone differences)
        token_exp = datetime.utcfromtimestamp(payload["exp"])
        assert abs((token_exp - custom_expiry).total_seconds()) < 60
    
    def test_refresh_token(self):
        """Test refresh token generation and usage."""
        jwt_manager = JWTManager(secret_key="test-secret")
        
        # Generate refresh token
        refresh_token = jwt_manager.generate_token(
            user_id="test@robco.com",
            email="test@robco.com",
            roles=["engineer"],
            token_type="refresh",
        )
        
        # Use refresh token to get new access token
        new_access_token = jwt_manager.refresh_token(refresh_token)
        
        assert new_access_token is not None
        
        # Validate new access token
        payload = jwt_manager.validate_token(new_access_token)
        assert payload["type"] == "access"


class TestRBACManager:
    """Test RBAC permission system."""
    
    def test_contractor_permissions(self):
        """Test contractor has limited permissions."""
        rbac = RBACManager()
        
        # Contractor should have workspace create permission
        assert rbac.has_permission(
            user_roles=["contractor"],
            required_permission=Permission.WORKSPACE_CREATE,
        )
        
        # Contractor should NOT have workspace delete permission
        assert not rbac.has_permission(
            user_roles=["contractor"],
            required_permission=Permission.WORKSPACE_DELETE,
        )
        
        # Contractor should NOT have blueprint create permission
        assert not rbac.has_permission(
            user_roles=["contractor"],
            required_permission=Permission.BLUEPRINT_CREATE,
        )
    
    def test_engineer_permissions(self):
        """Test engineer has standard permissions."""
        rbac = RBACManager()
        
        # Engineer should have full workspace permissions
        assert rbac.has_permission(
            user_roles=["engineer"],
            required_permission=Permission.WORKSPACE_CREATE,
        )
        assert rbac.has_permission(
            user_roles=["engineer"],
            required_permission=Permission.WORKSPACE_DELETE,
        )
        
        # Engineer should have blueprint create permission
        assert rbac.has_permission(
            user_roles=["engineer"],
            required_permission=Permission.BLUEPRINT_CREATE,
        )
        
        # Engineer should NOT have user management permissions
        assert not rbac.has_permission(
            user_roles=["engineer"],
            required_permission=Permission.USER_ASSIGN_ROLE,
        )
    
    def test_team_lead_permissions(self):
        """Test team lead has elevated permissions."""
        rbac = RBACManager()
        
        # Team lead should have all engineer permissions
        assert rbac.has_permission(
            user_roles=["team_lead"],
            required_permission=Permission.WORKSPACE_CREATE,
        )
        
        # Team lead should have budget update permission
        assert rbac.has_permission(
            user_roles=["team_lead"],
            required_permission=Permission.BUDGET_UPDATE,
        )
        
        # Team lead should have audit read permission
        assert rbac.has_permission(
            user_roles=["team_lead"],
            required_permission=Permission.AUDIT_READ,
        )
    
    def test_admin_permissions(self):
        """Test admin has all permissions."""
        rbac = RBACManager()
        
        # Admin should have all permissions
        assert rbac.has_permission(
            user_roles=["admin"],
            required_permission=Permission.WORKSPACE_CREATE,
        )
        assert rbac.has_permission(
            user_roles=["admin"],
            required_permission=Permission.USER_ASSIGN_ROLE,
        )
        assert rbac.has_permission(
            user_roles=["admin"],
            required_permission=Permission.BUDGET_OVERRIDE,
        )
    
    def test_bundle_type_restrictions(self):
        """Test bundle type access restrictions."""
        rbac = RBACManager()
        
        # Contractor can only access Standard and Performance
        assert rbac.check_bundle_access(["contractor"], "STANDARD")
        assert rbac.check_bundle_access(["contractor"], "PERFORMANCE")
        assert not rbac.check_bundle_access(["contractor"], "POWER")
        assert not rbac.check_bundle_access(["contractor"], "GRAPHICS_G4DN")
        assert not rbac.check_bundle_access(["contractor"], "GRAPHICSPRO_G4DN")
        
        # Engineer can access most bundles except GraphicsPro
        assert rbac.check_bundle_access(["engineer"], "STANDARD")
        assert rbac.check_bundle_access(["engineer"], "PERFORMANCE")
        assert rbac.check_bundle_access(["engineer"], "POWER")
        assert rbac.check_bundle_access(["engineer"], "GRAPHICS_G4DN")
        assert not rbac.check_bundle_access(["engineer"], "GRAPHICSPRO_G4DN")
        
        # Team lead can access all bundles
        assert rbac.check_bundle_access(["team_lead"], "GRAPHICSPRO_G4DN")
        
        # Admin can access all bundles
        assert rbac.check_bundle_access(["admin"], "GRAPHICSPRO_G4DN")
    
    def test_allowed_bundle_types(self):
        """Test getting list of allowed bundle types."""
        rbac = RBACManager()
        
        # Contractor allowed bundles
        contractor_bundles = rbac.get_allowed_bundle_types(["contractor"])
        assert set(contractor_bundles) == {"STANDARD", "PERFORMANCE"}
        
        # Engineer allowed bundles
        engineer_bundles = rbac.get_allowed_bundle_types(["engineer"])
        assert "GRAPHICSPRO_G4DN" not in engineer_bundles
        assert "GRAPHICS_G4DN" in engineer_bundles
        
        # Team lead allowed bundles
        team_lead_bundles = rbac.get_allowed_bundle_types(["team_lead"])
        assert "GRAPHICSPRO_G4DN" in team_lead_bundles
    
    def test_credential_expiry_enforcement(self):
        """Test that expired credentials are rejected."""
        rbac = RBACManager()
        
        # Expired credentials
        expired_time = datetime.utcnow() - timedelta(hours=1)
        
        # Should deny access even if permission exists
        assert not rbac.has_permission(
            user_roles=["contractor"],
            required_permission=Permission.WORKSPACE_CREATE,
            credential_expiry=expired_time,
        )
        
        # Valid credentials
        valid_time = datetime.utcnow() + timedelta(hours=1)
        
        # Should allow access
        assert rbac.has_permission(
            user_roles=["contractor"],
            required_permission=Permission.WORKSPACE_CREATE,
            credential_expiry=valid_time,
        )
    
    def test_multiple_roles(self):
        """Test user with multiple roles gets combined permissions."""
        rbac = RBACManager()
        
        # User with both engineer and team_lead roles
        permissions = rbac.get_permissions_for_roles(["engineer", "team_lead"])
        
        # Should have permissions from both roles
        assert Permission.WORKSPACE_CREATE in permissions
        assert Permission.BUDGET_UPDATE in permissions
        assert Permission.AUDIT_READ in permissions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

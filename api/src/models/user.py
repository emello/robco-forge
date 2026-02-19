"""User model for authentication and authorization."""

from sqlalchemy import Column, String, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class User(Base):
    """User entity for RobCo Forge platform.
    
    Requirements:
    - 8.3: RBAC role assignment
    - 8.5: Time-bound credentials for contractors
    """
    
    __tablename__ = "users"
    
    # Primary identification
    id = Column(String, primary_key=True)  # From Okta SAML NameID
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    
    # Role and permissions
    roles = Column(JSON, nullable=False, default=list)  # List of role names
    team_id = Column(String, index=True)  # Primary team membership
    
    # Contractor-specific fields
    is_contractor = Column(Boolean, default=False, index=True)
    credential_expiry = Column(DateTime)  # Time-bound credentials for contractors
    
    # Authentication metadata
    last_login = Column(DateTime)
    mfa_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Soft delete
    deleted_at = Column(DateTime)
    is_active = Column(Boolean, default=True, index=True)
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, roles={self.roles})>"
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role.
        
        Args:
            role: Role name to check
            
        Returns:
            True if user has the role, False otherwise
        """
        return role in self.roles
    
    def is_credentials_expired(self) -> bool:
        """Check if contractor credentials have expired.
        
        Returns:
            True if credentials expired, False otherwise
        """
        if not self.is_contractor or not self.credential_expiry:
            return False
        
        return datetime.utcnow() > self.credential_expiry

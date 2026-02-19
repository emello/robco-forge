"""AuditLog model - Requirements 10.1, 10.2"""
from datetime import datetime
from typing import Optional
import enum
from sqlalchemy import String, Text, DateTime, Enum, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class ActionType(str, enum.Enum):
    """Audit log action types"""
    # WorkSpace actions
    WORKSPACE_PROVISION = "WORKSPACE_PROVISION"
    WORKSPACE_START = "WORKSPACE_START"
    WORKSPACE_STOP = "WORKSPACE_STOP"
    WORKSPACE_TERMINATE = "WORKSPACE_TERMINATE"
    
    # Blueprint actions
    BLUEPRINT_CREATE = "BLUEPRINT_CREATE"
    BLUEPRINT_UPDATE = "BLUEPRINT_UPDATE"
    
    # Authentication actions
    AUTH_LOGIN = "AUTH_LOGIN"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    AUTH_FAILED = "AUTH_FAILED"
    
    # Lucy AI actions
    LUCY_PROVISION = "LUCY_PROVISION"
    LUCY_QUERY = "LUCY_QUERY"
    LUCY_ACTION = "LUCY_ACTION"
    
    # Budget actions
    BUDGET_WARNING = "BUDGET_WARNING"
    BUDGET_LIMIT_REACHED = "BUDGET_LIMIT_REACHED"
    
    # Other actions
    OTHER = "OTHER"


class ActionResult(str, enum.Enum):
    """Action result status"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    DENIED = "DENIED"


class AuditLog(Base):
    """
    AuditLog model for comprehensive audit logging with tamper-evident storage.
    
    Requirements:
    - 10.1: Log all platform actions with user identity, action, resource, result
    - 10.2: Include timestamp, engineer identity, action type, resource identifier, 
            action result, and source IP address
    - 10.3: Tamper-evident log storage with 7-year retention
    """
    __tablename__ = "audit_logs"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Timestamp (indexed for efficient queries)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    # User identity
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Action details
    action_type: Mapped[ActionType] = mapped_column(
        Enum(ActionType),
        nullable=False,
        index=True
    )
    action_description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Resource details
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # Action result
    result: Mapped[ActionResult] = mapped_column(
        Enum(ActionResult),
        nullable=False
    )
    
    # Network information
    source_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Interface used (portal, CLI, Lucy)
    interface: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Additional context (JSON for flexibility)
    context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Tamper-evident hash (computed from previous log entry)
    previous_log_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    log_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # Composite indexes for efficient queries
    __table_args__ = (
        Index('ix_audit_logs_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_audit_logs_action_timestamp', 'action_type', 'timestamp'),
        Index('ix_audit_logs_resource', 'resource_type', 'resource_id'),
        # Partitioning by month will be configured in Alembic migration
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action_type}, result={self.result})>"

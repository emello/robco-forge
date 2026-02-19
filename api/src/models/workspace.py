"""WorkSpace model - Requirements 1.1"""
from datetime import datetime
from typing import Optional
import enum
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin


class ServiceType(str, enum.Enum):
    """EUC service type"""
    WORKSPACES_PERSONAL = "WORKSPACES_PERSONAL"
    WORKSPACES_APPLICATIONS = "WORKSPACES_APPLICATIONS"


class BundleType(str, enum.Enum):
    """WorkSpace hardware configuration"""
    STANDARD = "STANDARD"  # 2 vCPU, 8 GB
    PERFORMANCE = "PERFORMANCE"  # 8 vCPU, 32 GB
    POWER = "POWER"  # 16 vCPU, 64 GB
    POWERPRO = "POWERPRO"  # 32 vCPU, 128 GB
    GRAPHICS_G4DN = "GRAPHICS_G4DN"  # 16 vCPU, 64 GB, NVIDIA T4
    GRAPHICSPRO_G4DN = "GRAPHICSPRO_G4DN"  # 64 vCPU, 256 GB, NVIDIA T4


class OperatingSystem(str, enum.Enum):
    """Operating system type"""
    WINDOWS = "WINDOWS"
    LINUX = "LINUX"


class WorkSpaceState(str, enum.Enum):
    """WorkSpace lifecycle state"""
    PENDING = "PENDING"
    AVAILABLE = "AVAILABLE"
    STOPPED = "STOPPED"
    STOPPING = "STOPPING"
    STARTING = "STARTING"
    TERMINATED = "TERMINATED"


class WorkSpace(Base, TimestampMixin):
    """
    WorkSpace model representing an AWS WorkSpaces instance.
    
    Requirements:
    - 1.1: Self-Service WorkSpace Provisioning
    - 1.7: Idle timeout enforcement
    - 1.9: Maximum lifetime enforcement
    """
    __tablename__ = "workspaces"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    
    # Service configuration
    service_type: Mapped[ServiceType] = mapped_column(
        Enum(ServiceType),
        nullable=False
    )
    bundle_type: Mapped[BundleType] = mapped_column(
        Enum(BundleType),
        nullable=False
    )
    operating_system: Mapped[OperatingSystem] = mapped_column(
        Enum(OperatingSystem),
        nullable=False
    )
    
    # Blueprint reference (optional for WorkSpaces Applications)
    blueprint_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("blueprints.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Application IDs for WorkSpaces Applications
    application_ids: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # State and region
    state: Mapped[WorkSpaceState] = mapped_column(
        Enum(WorkSpaceState),
        nullable=False,
        default=WorkSpaceState.PENDING
    )
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Network configuration
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    connection_url: Mapped[str] = mapped_column(String(512), nullable=False)
    
    # Domain join status
    domain_joined: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    domain_join_status: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # User and team ownership
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    team_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Cost tracking
    cost_to_date: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Lifecycle management (Requirements 1.7, 1.9)
    auto_stop_timeout_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_lifetime_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_connected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Stale workspace tracking (Requirement 14.2-14.5)
    keep_alive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stale_notification_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Cost allocation tags
    tags: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Relationships
    blueprint: Mapped[Optional["Blueprint"]] = relationship(
        "Blueprint",
        back_populates="workspaces"
    )
    cost_records: Mapped[list["CostRecord"]] = relationship(
        "CostRecord",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<WorkSpace(id={self.id}, state={self.state}, user_id={self.user_id})>"

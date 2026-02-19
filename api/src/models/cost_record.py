"""CostRecord model - Requirements 11.1, 16.4, 16.5"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Float, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class CostRecord(Base):
    """
    CostRecord model for tracking WorkSpace costs in real-time.
    
    Requirements:
    - 11.1: Real-time cost tracking per WorkSpace
    - 11.4: Cost calculation with 5-minute latency
    - 11.2: Cost aggregation by WorkSpace, user, team, project
    - 16.4: Support custom cost allocation tags
    - 16.5: Include tags in cost reports
    """
    __tablename__ = "cost_records"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # WorkSpace reference
    workspace_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Bundle type for breakdown
    bundle_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # User and team for aggregation
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    team_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Cost allocation tags (Requirements 16.4, 16.5)
    tags: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # Cost breakdown
    compute_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    storage_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    data_transfer_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    # Time period for this cost record
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    # Timestamp when record was created
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    # Relationships
    workspace: Mapped["WorkSpace"] = relationship(
        "WorkSpace",
        back_populates="cost_records"
    )
    
    # Composite indexes for efficient aggregation queries
    __table_args__ = (
        Index('ix_cost_records_user_period', 'user_id', 'period_start', 'period_end'),
        Index('ix_cost_records_team_period', 'team_id', 'period_start', 'period_end'),
        Index('ix_cost_records_workspace_period', 'workspace_id', 'period_start', 'period_end'),
    )
    
    def __repr__(self) -> str:
        return f"<CostRecord(id={self.id}, workspace_id={self.workspace_id}, total_cost={self.total_cost})>"

"""UserBudget model - Requirements 12.1"""
from datetime import datetime
from typing import Optional
import enum
from sqlalchemy import String, Float, DateTime, Enum, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin


class BudgetScope(str, enum.Enum):
    """Budget scope type"""
    USER = "USER"
    TEAM = "TEAM"
    PROJECT = "PROJECT"


class UserBudget(Base, TimestampMixin):
    """
    UserBudget model for budget tracking and enforcement.
    
    Requirements:
    - 12.1: Budget configuration per team, project, and individual engineer
    - 12.2: Warning at 80% threshold
    - 12.3: Hard limit at 100% threshold
    """
    __tablename__ = "user_budgets"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Budget scope
    scope: Mapped[BudgetScope] = mapped_column(
        Enum(BudgetScope),
        nullable=False
    )
    
    # Scope identifier (user_id, team_id, or project_id)
    scope_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Budget amount and period
    budget_amount: Mapped[float] = mapped_column(Float, nullable=False)
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    
    # Current spending
    current_spend: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Threshold tracking (Requirement 12.2)
    warning_threshold: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    warning_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    warning_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Hard limit enforcement (Requirement 12.3)
    hard_limit_reached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hard_limit_reached_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Ensure unique budget per scope and period
    __table_args__ = (
        UniqueConstraint('scope', 'scope_id', 'period_start', name='uq_budget_scope_period'),
    )
    
    @property
    def budget_utilization(self) -> float:
        """Calculate budget utilization percentage"""
        if self.budget_amount == 0:
            return 0.0
        return (self.current_spend / self.budget_amount) * 100
    
    @property
    def is_warning_threshold_reached(self) -> bool:
        """Check if warning threshold (80%) is reached"""
        return self.current_spend >= (self.budget_amount * self.warning_threshold)
    
    @property
    def is_hard_limit_reached(self) -> bool:
        """Check if hard limit (100%) is reached"""
        return self.current_spend >= self.budget_amount
    
    def __repr__(self) -> str:
        return f"<UserBudget(id={self.id}, scope={self.scope}, scope_id={self.scope_id}, utilization={self.budget_utilization:.1f}%)>"

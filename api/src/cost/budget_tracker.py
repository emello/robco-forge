"""Budget tracking service for RobCo Forge.

Requirements:
- 12.1: Budget configuration per team, project, and individual engineer
- 12.2: Warning at 80% threshold
- 12.3: Hard limit at 100% threshold
"""

from datetime import datetime
from typing import Optional, Tuple, Dict, Any
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.user_budget import UserBudget, BudgetScope
from ..models.cost_record import CostRecord

logger = logging.getLogger(__name__)


class BudgetExceededError(Exception):
    """Raised when budget limit is exceeded."""
    
    def __init__(self, message: str, budget_info: Dict[str, Any]):
        super().__init__(message)
        self.budget_info = budget_info


class BudgetTracker:
    """
    Budget tracking service for enforcing spending limits.
    
    Validates:
    - Requirements 12.1: Budget configuration per team, project, and individual engineer
    - Requirements 12.2: Warning at 80% threshold
    - Requirements 12.3: Hard limit at 100% threshold
    """
    
    def __init__(self, db: Session):
        """Initialize budget tracker.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_budget(
        self,
        scope: BudgetScope,
        scope_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        use_current_period: bool = True
    ) -> Optional[UserBudget]:
        """Get budget for a specific scope and period.
        
        Args:
            scope: Budget scope (USER, TEAM, PROJECT)
            scope_id: Scope identifier
            period_start: Period start date (for specific period lookup)
            period_end: Period end date (for specific period lookup)
            use_current_period: If True and no period specified, find budget active now
            
        Returns:
            UserBudget if found, None otherwise
        """
        query = self.db.query(UserBudget).filter(
            and_(
                UserBudget.scope == scope,
                UserBudget.scope_id == scope_id
            )
        )
        
        # Filter by period if provided
        if period_start and period_end:
            query = query.filter(
                and_(
                    UserBudget.period_start <= period_start,
                    UserBudget.period_end >= period_end
                )
            )
        elif use_current_period:
            # Get current period budget
            now = datetime.now()
            query = query.filter(
                and_(
                    UserBudget.period_start <= now,
                    UserBudget.period_end >= now
                )
            )
        # If use_current_period is False and no period specified, return first match
        
        return query.first()
    
    def update_budget_spend(
        self,
        scope: BudgetScope,
        scope_id: str,
        amount: float
    ) -> UserBudget:
        """Update budget spending.
        
        Args:
            scope: Budget scope
            scope_id: Scope identifier
            amount: Amount to add to current spend
            
        Returns:
            Updated budget
            
        Raises:
            ValueError: If budget not found
        """
        budget = self.get_budget(scope, scope_id, use_current_period=False)
        
        if not budget:
            raise ValueError(f"No budget found for {scope.value} {scope_id}")
        
        # Update spend
        budget.current_spend += amount
        
        # Check thresholds
        if budget.is_warning_threshold_reached and not budget.warning_sent:
            budget.warning_sent = True
            budget.warning_sent_at = datetime.now()
            logger.warning(
                f"budget_warning_threshold_reached scope={scope.value} "
                f"scope_id={scope_id} current_spend={budget.current_spend} "
                f"budget_amount={budget.budget_amount} utilization={budget.budget_utilization}"
            )
            # TODO: Send notification (will be implemented in notification service)
        
        if budget.is_hard_limit_reached and not budget.hard_limit_reached:
            budget.hard_limit_reached = True
            budget.hard_limit_reached_at = datetime.now()
            logger.error(
                f"budget_hard_limit_reached scope={scope.value} "
                f"scope_id={scope_id} current_spend={budget.current_spend} "
                f"budget_amount={budget.budget_amount}"
            )
            # TODO: Send notification (will be implemented in notification service)
        
        self.db.commit()
        self.db.refresh(budget)
        
        return budget
    
    def check_budget(
        self,
        user_id: str,
        team_id: str,
        project_id: Optional[str],
        estimated_cost: float
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Check if provisioning would exceed budget limits.
        
        Validates: Requirements 12.3 (Hard limit at 100%)
        
        Checks budgets in order: user -> team -> project
        Returns on first budget that would be exceeded.
        
        Args:
            user_id: User identifier
            team_id: Team identifier
            project_id: Project identifier (optional)
            estimated_cost: Estimated cost of the action
            
        Returns:
            Tuple of (allowed, warning_message, budget_info)
            - allowed: True if action is allowed, False if blocked
            - warning_message: Warning message if at 80% threshold, None otherwise
            - budget_info: Budget information dict if blocked, None otherwise
        """
        # Check user budget
        user_budget = self.get_budget(BudgetScope.USER, user_id, use_current_period=False)
        if user_budget:
            result = self._check_single_budget(user_budget, estimated_cost, "user")
            if not result[0]:  # Blocked
                return result
        
        # Check team budget
        team_budget = self.get_budget(BudgetScope.TEAM, team_id, use_current_period=False)
        if team_budget:
            result = self._check_single_budget(team_budget, estimated_cost, "team")
            if not result[0]:  # Blocked
                return result
        
        # Check project budget if provided
        if project_id:
            project_budget = self.get_budget(BudgetScope.PROJECT, project_id, use_current_period=False)
            if project_budget:
                result = self._check_single_budget(project_budget, estimated_cost, "project")
                if not result[0]:  # Blocked
                    return result
        
        # Collect warnings from all budgets (check projected spend)
        warnings = []
        
        if user_budget:
            projected_user_spend = user_budget.current_spend + estimated_cost
            if projected_user_spend >= (user_budget.budget_amount * user_budget.warning_threshold):
                warnings.append(
                    f"User budget at {(projected_user_spend / user_budget.budget_amount) * 100:.1f}% "
                    f"(${projected_user_spend:.2f} / ${user_budget.budget_amount:.2f})"
                )
        
        if team_budget:
            projected_team_spend = team_budget.current_spend + estimated_cost
            if projected_team_spend >= (team_budget.budget_amount * team_budget.warning_threshold):
                warnings.append(
                    f"Team budget at {(projected_team_spend / team_budget.budget_amount) * 100:.1f}% "
                    f"(${projected_team_spend:.2f} / ${team_budget.budget_amount:.2f})"
                )
        
        if project_id and project_budget:
            projected_project_spend = project_budget.current_spend + estimated_cost
            if projected_project_spend >= (project_budget.budget_amount * project_budget.warning_threshold):
                warnings.append(
                    f"Project budget at {(projected_project_spend / project_budget.budget_amount) * 100:.1f}% "
                    f"(${projected_project_spend:.2f} / ${project_budget.budget_amount:.2f})"
                )
        
        warning_message = "; ".join(warnings) if warnings else None
        
        return True, warning_message, None
    
    def _check_single_budget(
        self,
        budget: UserBudget,
        estimated_cost: float,
        scope_name: str
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Check a single budget against estimated cost.
        
        Args:
            budget: Budget to check
            estimated_cost: Estimated cost
            scope_name: Scope name for error messages
            
        Returns:
            Tuple of (allowed, warning_message, budget_info)
        """
        projected_spend = budget.current_spend + estimated_cost
        
        # Check hard limit (100%)
        if projected_spend >= budget.budget_amount:
            budget_info = {
                "scope": scope_name,
                "scope_id": budget.scope_id,
                "budget_amount": budget.budget_amount,
                "current_spend": budget.current_spend,
                "projected_spend": projected_spend,
                "estimated_cost": estimated_cost,
                "utilization": (projected_spend / budget.budget_amount) * 100,
                "period_start": budget.period_start.isoformat(),
                "period_end": budget.period_end.isoformat(),
            }
            
            message = (
                f"Budget exceeded: {scope_name} budget limit reached. "
                f"Current: ${budget.current_spend:.2f}, "
                f"Estimated cost: ${estimated_cost:.2f}, "
                f"Budget: ${budget.budget_amount:.2f}"
            )
            
            logger.warning(
                f"budget_check_failed scope={scope_name} scope_id={budget.scope_id} "
                f"current_spend={budget.current_spend} estimated_cost={estimated_cost} "
                f"budget_amount={budget.budget_amount} projected_spend={projected_spend}"
            )
            
            return False, message, budget_info
        
        # Check warning threshold (80%)
        warning_threshold_amount = budget.budget_amount * budget.warning_threshold
        if projected_spend >= warning_threshold_amount:
            warning_message = (
                f"Warning: {scope_name} budget at "
                f"{(projected_spend / budget.budget_amount) * 100:.1f}% "
                f"(${projected_spend:.2f} / ${budget.budget_amount:.2f})"
            )
            return True, warning_message, None
        
        return True, None, None
    
    def create_budget(
        self,
        scope: BudgetScope,
        scope_id: str,
        budget_amount: float,
        period_start: datetime,
        period_end: datetime,
        warning_threshold: float = 0.8
    ) -> UserBudget:
        """Create a new budget.
        
        Validates: Requirements 12.1
        
        Args:
            scope: Budget scope
            scope_id: Scope identifier
            budget_amount: Budget amount
            period_start: Period start date
            period_end: Period end date
            warning_threshold: Warning threshold (default 0.8 = 80%)
            
        Returns:
            Created budget
            
        Raises:
            ValueError: If budget already exists for this scope and period
        """
        # Check if budget already exists
        existing = self.db.query(UserBudget).filter(
            and_(
                UserBudget.scope == scope,
                UserBudget.scope_id == scope_id,
                UserBudget.period_start == period_start
            )
        ).first()
        
        if existing:
            raise ValueError(
                f"Budget already exists for {scope.value} {scope_id} "
                f"starting {period_start.isoformat()}"
            )
        
        budget = UserBudget(
            scope=scope,
            scope_id=scope_id,
            budget_amount=budget_amount,
            period_start=period_start,
            period_end=period_end,
            warning_threshold=warning_threshold,
            current_spend=0.0,
            warning_sent=False,
            hard_limit_reached=False
        )
        
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        
        logger.info(
            f"budget_created scope={scope.value} scope_id={scope_id} "
            f"budget_amount={budget_amount} period_start={period_start.isoformat()} "
            f"period_end={period_end.isoformat()}"
        )
        
        return budget
    
    def get_budget_status(
        self,
        scope: BudgetScope,
        scope_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get current budget status.
        
        Args:
            scope: Budget scope
            scope_id: Scope identifier
            
        Returns:
            Budget status dict or None if no budget found
        """
        budget = self.get_budget(scope, scope_id, use_current_period=False)
        
        if not budget:
            return None
        
        return {
            "scope": budget.scope.value,
            "scope_id": budget.scope_id,
            "budget_amount": budget.budget_amount,
            "current_spend": budget.current_spend,
            "remaining": budget.budget_amount - budget.current_spend,
            "utilization": budget.budget_utilization,
            "warning_threshold_reached": budget.is_warning_threshold_reached,
            "hard_limit_reached": budget.is_hard_limit_reached,
            "period_start": budget.period_start.isoformat(),
            "period_end": budget.period_end.isoformat(),
        }

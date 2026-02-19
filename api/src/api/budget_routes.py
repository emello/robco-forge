"""Budget management API routes.

Requirements:
- 12.1: Budget configuration per team, project, and individual engineer
- 12.2: Warning at 80% threshold
- 12.3: Hard limit at 100% threshold
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import Permission
from ..api.auth_routes import get_current_user, require_permission
from ..database import get_db
from ..models.user_budget import BudgetScope
from ..cost.budget_tracker import BudgetTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/budgets", tags=["budgets"])


# Request/Response models
class BudgetStatusResponse(BaseModel):
    """Budget status response."""
    scope: str
    scope_id: str
    budget_amount: float
    current_spend: float
    remaining: float
    utilization: float
    warning_threshold_reached: bool
    hard_limit_reached: bool
    period_start: str
    period_end: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "scope": "USER",
                "scope_id": "user-123",
                "budget_amount": 1000.0,
                "current_spend": 750.0,
                "remaining": 250.0,
                "utilization": 75.0,
                "warning_threshold_reached": False,
                "hard_limit_reached": False,
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-31T23:59:59Z"
            }
        }


class BudgetCheckRequest(BaseModel):
    """Request to check if an action would exceed budget."""
    estimated_cost: float = Field(..., description="Estimated cost of the action")
    project_id: Optional[str] = Field(None, description="Project ID (optional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "estimated_cost": 50.0,
                "project_id": "sim-engine"
            }
        }


class BudgetCheckResponse(BaseModel):
    """Response for budget check."""
    allowed: bool
    warning_message: Optional[str]
    budget_info: Optional[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "allowed": True,
                "warning_message": "User budget at 85.0% ($850.00 / $1000.00)",
                "budget_info": None
            }
        }


# Routes
@router.get("/user", response_model=BudgetStatusResponse)
async def get_user_budget(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.WORKSPACE_READ)),
):
    """Get current user's budget status.
    
    Returns the budget status for the authenticated user.
    
    Requirements:
    - Validates: Requirements 12.1 (Budget configuration)
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        User budget status
        
    Raises:
        HTTPException: If no budget found
    """
    try:
        budget_tracker = BudgetTracker(db)
        budget_status = budget_tracker.get_budget_status(
            scope=BudgetScope.USER,
            scope_id=current_user["user_id"]
        )
        
        if not budget_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No budget configured for user"
            )
        
        return budget_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user budget: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user budget: {str(e)}"
        )


@router.get("/team", response_model=BudgetStatusResponse)
async def get_team_budget(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.WORKSPACE_READ)),
):
    """Get current user's team budget status.
    
    Returns the budget status for the user's team.
    
    Requirements:
    - Validates: Requirements 12.1 (Budget configuration)
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Team budget status
        
    Raises:
        HTTPException: If no budget found
    """
    try:
        team_id = current_user.get("team_id", "default")
        
        budget_tracker = BudgetTracker(db)
        budget_status = budget_tracker.get_budget_status(
            scope=BudgetScope.TEAM,
            scope_id=team_id
        )
        
        if not budget_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No budget configured for team {team_id}"
            )
        
        return budget_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team budget: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team budget: {str(e)}"
        )


@router.post("/check", response_model=BudgetCheckResponse)
async def check_budget(
    request: BudgetCheckRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.WORKSPACE_READ)),
):
    """Check if an action would exceed budget limits.
    
    Validates if a proposed action with estimated cost would exceed
    user, team, or project budget limits.
    
    Requirements:
    - Validates: Requirements 12.3 (Hard limit at 100%)
    
    Args:
        request: Budget check request
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Budget check result
    """
    try:
        budget_tracker = BudgetTracker(db)
        
        allowed, warning_message, budget_info = budget_tracker.check_budget(
            user_id=current_user["user_id"],
            team_id=current_user.get("team_id", "default"),
            project_id=request.project_id,
            estimated_cost=request.estimated_cost
        )
        
        return BudgetCheckResponse(
            allowed=allowed,
            warning_message=warning_message,
            budget_info=budget_info
        )
        
    except Exception as e:
        logger.error(f"Failed to check budget: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check budget: {str(e)}"
        )

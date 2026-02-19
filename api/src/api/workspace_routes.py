"""WorkSpace management API routes.

Requirements:
- 1.1: Self-service WorkSpace provisioning
- 1.7: Auto-stop on idle timeout
- 1.9: Auto-terminate at maximum lifetime
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import Permission
from ..auth.rbac import RBACManager
from ..api.auth_routes import get_current_user, require_permission
from ..database import get_db
from ..models.workspace import WorkSpace, WorkSpaceState
from ..models.user_budget import BudgetScope
from ..cost.budget_tracker import BudgetTracker
from ..cost.cost_calculator import CostCalculator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])


# Request/Response models
class ProvisionWorkSpaceRequest(BaseModel):
    """Request to provision a new WorkSpace."""
    service_type: str = Field(..., description="WORKSPACES_PERSONAL or WORKSPACES_APPLICATIONS")
    bundle_type: str = Field(..., description="Bundle type (STANDARD, PERFORMANCE, POWER, etc.)")
    operating_system: str = Field(..., description="Operating system (WINDOWS or LINUX)")
    blueprint_id: Optional[str] = Field(None, description="Blueprint ID for WorkSpaces Personal")
    application_ids: Optional[List[str]] = Field(None, description="Application IDs for WorkSpaces Applications")
    tags: Optional[Dict[str, str]] = Field(default_factory=dict, description="Custom tags")
    auto_stop_timeout_minutes: Optional[int] = Field(60, description="Auto-stop timeout in minutes")
    max_lifetime_days: Optional[int] = Field(90, description="Maximum lifetime in days")
    
    class Config:
        json_schema_extra = {
            "example": {
                "service_type": "WORKSPACES_PERSONAL",
                "bundle_type": "PERFORMANCE",
                "operating_system": "LINUX",
                "blueprint_id": "robotics-v3",
                "tags": {"project": "sim-engine", "team": "robotics-ai"},
                "auto_stop_timeout_minutes": 60,
                "max_lifetime_days": 90
            }
        }


class WorkSpaceResponse(BaseModel):
    """WorkSpace response model."""
    id: str
    user_id: str
    team_id: str
    service_type: str
    bundle_type: str
    operating_system: str
    blueprint_id: Optional[str]
    application_ids: Optional[List[str]]
    region: str
    state: str
    ip_address: Optional[str]
    connection_url: Optional[str]
    domain_joined: bool
    domain_join_status: Optional[str]
    auto_stop_timeout_minutes: int
    max_lifetime_days: int
    created_at: datetime
    last_connected_at: Optional[datetime]
    last_stopped_at: Optional[datetime]
    terminated_at: Optional[datetime]
    cost_to_date: float
    tags: Dict[str, str]
    
    class Config:
        from_attributes = True


class WorkSpaceListResponse(BaseModel):
    """List of WorkSpaces response."""
    workspaces: List[WorkSpaceResponse]
    total: int
    page: int
    page_size: int


class WorkSpaceActionResponse(BaseModel):
    """Response for WorkSpace actions (start, stop, terminate)."""
    workspace_id: str
    action: str
    status: str
    message: str


# Helper functions
def check_bundle_access(user_roles: List[str], bundle_type: str, rbac_manager: RBACManager):
    """Check if user can access the requested bundle type.
    
    Validates: Requirements 8.6
    """
    if not rbac_manager.check_bundle_access(user_roles, bundle_type):
        allowed_bundles = rbac_manager.get_allowed_bundle_types(user_roles)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "BUNDLE_ACCESS_DENIED",
                    "message": f"You do not have permission to use {bundle_type} bundle type",
                    "details": {
                        "requested_bundle": bundle_type,
                        "allowed_bundles": allowed_bundles,
                    },
                    "retryable": False,
                    "suggested_action": f"Use one of the allowed bundle types: {', '.join(allowed_bundles)}"
                }
            }
        )


# Routes
@router.post("", response_model=WorkSpaceResponse, status_code=status.HTTP_201_CREATED)
async def provision_workspace(
    request: ProvisionWorkSpaceRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.WORKSPACE_CREATE)),
    rbac_manager: RBACManager = Depends(lambda: RBACManager()),
):
    """Provision a new WorkSpace.
    
    Creates a new WorkSpace instance based on the provided configuration.
    
    Requirements:
    - Validates: Requirements 1.1 (Self-service provisioning)
    - Validates: Requirements 8.6 (Bundle type restrictions)
    
    Args:
        request: WorkSpace provisioning request
        db: Database session
        current_user: Current authenticated user
        rbac_manager: RBAC manager
        
    Returns:
        Created WorkSpace details
        
    Raises:
        HTTPException: If bundle access denied or provisioning fails
    """
    try:
        # Check bundle type access
        check_bundle_access(current_user["roles"], request.bundle_type, rbac_manager)
        
        # Validate service type
        valid_service_types = ["WORKSPACES_PERSONAL", "WORKSPACES_APPLICATIONS"]
        if request.service_type not in valid_service_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid service_type. Must be one of: {', '.join(valid_service_types)}"
            )
        
        # Validate operating system
        valid_os = ["WINDOWS", "LINUX"]
        if request.operating_system not in valid_os:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid operating_system. Must be one of: {', '.join(valid_os)}"
            )
        
        # Validate bundle type
        valid_bundles = ["STANDARD", "PERFORMANCE", "POWER", "POWERPRO", "GRAPHICS_G4DN", "GRAPHICSPRO_G4DN"]
        if request.bundle_type not in valid_bundles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid bundle_type. Must be one of: {', '.join(valid_bundles)}"
            )
        
        # Check budget before provisioning (Requirements 12.3, 12.4)
        budget_tracker = BudgetTracker(db)
        cost_calculator = CostCalculator()
        
        # Estimate cost for this workspace (daily cost)
        estimated_daily_cost = cost_calculator.estimate_daily_cost(
            bundle_type=request.bundle_type,
            storage_gb=100,  # Default storage estimate
            operating_system=request.operating_system
        )
        
        # Get project_id from tags if provided
        project_id = request.tags.get("project") if request.tags else None
        
        # Check budget limits
        allowed, warning_message, budget_info = budget_tracker.check_budget(
            user_id=current_user["user_id"],
            team_id=current_user.get("team_id", "default"),
            project_id=project_id,
            estimated_cost=estimated_daily_cost
        )
        
        if not allowed:
            # Budget exceeded - block provisioning (Requirement 12.3)
            logger.warning(
                "provisioning_blocked_budget_exceeded",
                user_id=current_user["user_id"],
                budget_info=budget_info
            )
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": {
                        "code": "BUDGET_EXCEEDED",
                        "message": "Cannot provision WorkSpace: budget limit reached",
                        "details": budget_info,
                        "retryable": False,
                        "suggested_action": "Contact your team lead or finance manager to increase budget allocation"
                    }
                }
            )
        
        # Log warning if approaching budget limit (Requirement 12.2)
        if warning_message:
            logger.warning(
                "budget_warning_on_provision",
                user_id=current_user["user_id"],
                warning=warning_message,
                estimated_cost=estimated_daily_cost
            )
        
        # TODO: Select optimal region based on user location (will be implemented in Task 9)
        # TODO: Check pre-warmed pool availability (will be implemented in Task 13)
        
        # Create WorkSpace record
        workspace = WorkSpace(
            id=f"ws-{uuid4().hex[:12]}",
            user_id=current_user["user_id"],
            team_id=current_user.get("team_id", "default"),  # TODO: Get from user profile
            service_type=request.service_type,
            bundle_type=request.bundle_type,
            operating_system=request.operating_system,
            blueprint_id=request.blueprint_id,
            application_ids=request.application_ids,
            region="us-west-2",  # TODO: Implement region selection
            state=WorkSpaceState.PENDING,
            domain_joined=False,
            domain_join_status="PENDING",
            auto_stop_timeout_minutes=request.auto_stop_timeout_minutes,
            max_lifetime_days=request.max_lifetime_days,
            created_at=datetime.utcnow(),
            tags=request.tags,
        )
        
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
        
        logger.info(
            "workspace_provisioned",
            workspace_id=workspace.id,
            user_id=current_user["user_id"],
            bundle_type=request.bundle_type,
            service_type=request.service_type,
        )
        
        # TODO: Trigger async provisioning task (will be implemented in Task 9)
        # This would call the Provisioning Service to actually create the WorkSpace
        
        return workspace
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to provision workspace: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "PROVISIONING_FAILED",
                    "message": f"Failed to provision WorkSpace: {str(e)}",
                    "retryable": True,
                }
            }
        )


@router.get("", response_model=WorkSpaceListResponse)
async def list_workspaces(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    state: Optional[str] = Query(None, description="Filter by state"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.WORKSPACE_READ)),
):
    """List user's WorkSpaces.
    
    Returns a paginated list of WorkSpaces owned by the current user.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        state: Optional state filter
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Paginated list of WorkSpaces
    """
    try:
        # Build query
        query = db.query(WorkSpace).filter(WorkSpace.user_id == current_user["user_id"])
        
        # Apply state filter if provided
        if state:
            try:
                state_enum = WorkSpaceState[state.upper()]
                query = query.filter(WorkSpace.state == state_enum)
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid state: {state}"
                )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        workspaces = query.offset(offset).limit(page_size).all()
        
        return WorkSpaceListResponse(
            workspaces=workspaces,
            total=total,
            page=page,
            page_size=page_size,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list workspaces: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workspaces: {str(e)}"
        )


@router.get("/{workspace_id}", response_model=WorkSpaceResponse)
async def get_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.WORKSPACE_READ)),
):
    """Get WorkSpace details.
    
    Returns detailed information about a specific WorkSpace.
    
    Args:
        workspace_id: WorkSpace ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        WorkSpace details
        
    Raises:
        HTTPException: If WorkSpace not found or access denied
    """
    try:
        workspace = db.query(WorkSpace).filter(WorkSpace.id == workspace_id).first()
        
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"WorkSpace not found: {workspace_id}"
            )
        
        # Check ownership
        if workspace.user_id != current_user["user_id"]:
            # TODO: Check if user is team lead or admin
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this WorkSpace"
            )
        
        return workspace
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workspace: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace: {str(e)}"
        )


@router.post("/{workspace_id}/start", response_model=WorkSpaceActionResponse)
async def start_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.WORKSPACE_START)),
):
    """Start a stopped WorkSpace.
    
    Transitions a WorkSpace from STOPPED to STARTING state.
    
    Args:
        workspace_id: WorkSpace ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Action response
        
    Raises:
        HTTPException: If WorkSpace not found, access denied, or invalid state
    """
    try:
        workspace = db.query(WorkSpace).filter(WorkSpace.id == workspace_id).first()
        
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"WorkSpace not found: {workspace_id}"
            )
        
        # Check ownership
        if workspace.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to start this WorkSpace"
            )
        
        # Check state
        if workspace.state != WorkSpaceState.STOPPED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot start WorkSpace in {workspace.state.value} state. Must be STOPPED."
            )
        
        # Update state
        workspace.state = WorkSpaceState.STARTING
        db.commit()
        
        logger.info(
            "workspace_start_initiated",
            workspace_id=workspace_id,
            user_id=current_user["user_id"],
        )
        
        # TODO: Trigger async start task (will be implemented in Task 9)
        
        return WorkSpaceActionResponse(
            workspace_id=workspace_id,
            action="start",
            status="initiated",
            message=f"WorkSpace {workspace_id} is starting"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start workspace: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workspace: {str(e)}"
        )


@router.post("/{workspace_id}/stop", response_model=WorkSpaceActionResponse)
async def stop_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.WORKSPACE_STOP)),
):
    """Stop a running WorkSpace.
    
    Transitions a WorkSpace from AVAILABLE to STOPPING state.
    
    Validates: Requirements 1.7 (Auto-stop on idle timeout)
    
    Args:
        workspace_id: WorkSpace ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Action response
        
    Raises:
        HTTPException: If WorkSpace not found, access denied, or invalid state
    """
    try:
        workspace = db.query(WorkSpace).filter(WorkSpace.id == workspace_id).first()
        
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"WorkSpace not found: {workspace_id}"
            )
        
        # Check ownership
        if workspace.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to stop this WorkSpace"
            )
        
        # Check state
        if workspace.state != WorkSpaceState.AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot stop WorkSpace in {workspace.state.value} state. Must be AVAILABLE."
            )
        
        # Update state
        workspace.state = WorkSpaceState.STOPPING
        workspace.last_stopped_at = datetime.utcnow()
        db.commit()
        
        logger.info(
            "workspace_stop_initiated",
            workspace_id=workspace_id,
            user_id=current_user["user_id"],
        )
        
        # TODO: Trigger async stop task (will be implemented in Task 9)
        
        return WorkSpaceActionResponse(
            workspace_id=workspace_id,
            action="stop",
            status="initiated",
            message=f"WorkSpace {workspace_id} is stopping"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop workspace: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop workspace: {str(e)}"
        )


@router.delete("/{workspace_id}", response_model=WorkSpaceActionResponse)
async def terminate_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.WORKSPACE_DELETE)),
):
    """Terminate a WorkSpace.
    
    Permanently terminates a WorkSpace. This action cannot be undone.
    
    Validates: Requirements 1.9 (Auto-terminate at maximum lifetime)
    
    Args:
        workspace_id: WorkSpace ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Action response
        
    Raises:
        HTTPException: If WorkSpace not found or access denied
    """
    try:
        workspace = db.query(WorkSpace).filter(WorkSpace.id == workspace_id).first()
        
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"WorkSpace not found: {workspace_id}"
            )
        
        # Check ownership
        if workspace.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to terminate this WorkSpace"
            )
        
        # Check if already terminated
        if workspace.state == WorkSpaceState.TERMINATED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"WorkSpace {workspace_id} is already terminated"
            )
        
        # Update state
        workspace.state = WorkSpaceState.TERMINATED
        workspace.terminated_at = datetime.utcnow()
        db.commit()
        
        logger.info(
            "workspace_terminated",
            workspace_id=workspace_id,
            user_id=current_user["user_id"],
        )
        
        # TODO: Trigger async termination task (will be implemented in Task 9)
        
        return WorkSpaceActionResponse(
            workspace_id=workspace_id,
            action="terminate",
            status="completed",
            message=f"WorkSpace {workspace_id} has been terminated"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to terminate workspace: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to terminate workspace: {str(e)}"
        )

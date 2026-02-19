"""Blueprint management API routes.

Requirements:
- 2.1: Blueprint version control
- 2.2: Blueprint creation
- 2.3: Blueprint versioning (immutability)
- 2.4: Team-scoped access control
- 2.5: Blueprint filtering by team membership
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import Permission
from ..api.auth_routes import get_current_user, require_permission
from ..database import get_db
from ..models.blueprint import Blueprint

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/blueprints", tags=["blueprints"])


# Request/Response models
class CreateBlueprintRequest(BaseModel):
    """Request to create a new Blueprint."""
    name: str = Field(..., description="Blueprint name")
    description: Optional[str] = Field(None, description="Blueprint description")
    operating_system: str = Field(..., description="Operating system (WINDOWS or LINUX)")
    bundle_image_id: str = Field(..., description="WorkSpaces Custom Bundle ID")
    software_manifest: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Installed software list")
    configuration: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Environment variables and settings")
    team_id: Optional[str] = Field(None, description="Team ID for team-scoped blueprints (None for global)")
    is_public: bool = Field(False, description="Whether blueprint is publicly accessible")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Robotics Development v3",
                "description": "Development environment for robotics simulation",
                "operating_system": "LINUX",
                "bundle_image_id": "wsb-abc123def456",
                "software_manifest": {
                    "python": "3.11",
                    "ros2": "humble",
                    "gazebo": "11.0"
                },
                "configuration": {
                    "ROS_DOMAIN_ID": "42",
                    "GAZEBO_MODEL_PATH": "/opt/gazebo/models"
                },
                "team_id": "robotics-ai",
                "is_public": False
            }
        }


class UpdateBlueprintRequest(BaseModel):
    """Request to update a Blueprint (creates new version)."""
    description: Optional[str] = None
    bundle_image_id: Optional[str] = None
    software_manifest: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class BlueprintResponse(BaseModel):
    """Blueprint response model."""
    id: str
    name: str
    description: Optional[str]
    version: str
    operating_system: str
    team_id: Optional[str]
    bundle_image_id: str
    software_manifest: Dict[str, Any]
    configuration: Dict[str, Any]
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    is_public: bool
    
    class Config:
        from_attributes = True


class BlueprintListResponse(BaseModel):
    """List of Blueprints response."""
    blueprints: List[BlueprintResponse]
    total: int
    page: int
    page_size: int


# Helper functions
def check_blueprint_access(blueprint: Blueprint, user_id: str, user_roles: List[str], team_id: Optional[str]) -> bool:
    """Check if user can access a blueprint.
    
    Validates: Requirements 2.4, 2.5
    
    Args:
        blueprint: Blueprint to check
        user_id: User ID
        user_roles: User roles
        team_id: User's team ID
        
    Returns:
        True if user can access, False otherwise
    """
    # Public blueprints are accessible to all
    if blueprint.is_public:
        return True
    
    # Global blueprints (no team_id) are accessible to all
    if blueprint.team_id is None:
        return True
    
    # Team-scoped blueprints require team membership
    if blueprint.team_id == team_id:
        return True
    
    # Admins can access all blueprints
    if "admin" in user_roles:
        return True
    
    return False


# Routes
@router.post("", response_model=BlueprintResponse, status_code=status.HTTP_201_CREATED)
async def create_blueprint(
    request: CreateBlueprintRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.BLUEPRINT_CREATE)),
):
    """Create a new Blueprint.
    
    Creates a new Blueprint with version 1.0.0.
    
    Validates: Requirements 2.1, 2.2
    
    Args:
        request: Blueprint creation request
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created Blueprint details
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        # Validate operating system
        valid_os = ["WINDOWS", "LINUX"]
        if request.operating_system not in valid_os:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid operating_system. Must be one of: {', '.join(valid_os)}"
            )
        
        # Check if blueprint name already exists for this team
        existing = db.query(Blueprint).filter(
            Blueprint.name == request.name,
            Blueprint.team_id == request.team_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Blueprint with name '{request.name}' already exists for this team"
            )
        
        # Create Blueprint
        blueprint = Blueprint(
            id=f"bp-{uuid4().hex[:12]}",
            name=request.name,
            description=request.description,
            version="1.0.0",
            operating_system=request.operating_system,
            team_id=request.team_id,
            bundle_image_id=request.bundle_image_id,
            software_manifest=request.software_manifest,
            configuration=request.configuration,
            created_by=current_user["user_id"],
            created_at=datetime.utcnow(),
            is_active=True,
            is_public=request.is_public,
        )
        
        db.add(blueprint)
        db.commit()
        db.refresh(blueprint)
        
        logger.info(
            "blueprint_created",
            blueprint_id=blueprint.id,
            name=blueprint.name,
            version=blueprint.version,
            created_by=current_user["user_id"],
        )
        
        return blueprint
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create blueprint: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create blueprint: {str(e)}"
        )


@router.get("", response_model=BlueprintListResponse)
async def list_blueprints(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    operating_system: Optional[str] = Query(None, description="Filter by OS"),
    team_id: Optional[str] = Query(None, description="Filter by team"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.BLUEPRINT_READ)),
):
    """List available Blueprints.
    
    Returns Blueprints accessible to the current user based on team membership.
    
    Validates: Requirements 2.5
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        operating_system: Optional OS filter
        team_id: Optional team filter
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Paginated list of Blueprints
    """
    try:
        user_team_id = current_user.get("team_id")
        user_roles = current_user.get("roles", [])
        
        # Build query - only active blueprints
        query = db.query(Blueprint).filter(Blueprint.is_active == True)
        
        # Apply OS filter if provided
        if operating_system:
            query = query.filter(Blueprint.operating_system == operating_system.upper())
        
        # Apply team filter if provided
        if team_id:
            query = query.filter(Blueprint.team_id == team_id)
        
        # Get all blueprints (we'll filter by access in Python)
        all_blueprints = query.all()
        
        # Filter by access
        accessible_blueprints = [
            bp for bp in all_blueprints
            if check_blueprint_access(bp, current_user["user_id"], user_roles, user_team_id)
        ]
        
        # Apply pagination
        total = len(accessible_blueprints)
        offset = (page - 1) * page_size
        blueprints = accessible_blueprints[offset:offset + page_size]
        
        return BlueprintListResponse(
            blueprints=blueprints,
            total=total,
            page=page,
            page_size=page_size,
        )
        
    except Exception as e:
        logger.error(f"Failed to list blueprints: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list blueprints: {str(e)}"
        )


@router.get("/{blueprint_id}", response_model=BlueprintResponse)
async def get_blueprint(
    blueprint_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.BLUEPRINT_READ)),
):
    """Get Blueprint details.
    
    Returns detailed information about a specific Blueprint.
    
    Validates: Requirements 2.4
    
    Args:
        blueprint_id: Blueprint ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Blueprint details
        
    Raises:
        HTTPException: If Blueprint not found or access denied
    """
    try:
        blueprint = db.query(Blueprint).filter(Blueprint.id == blueprint_id).first()
        
        if not blueprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Blueprint not found: {blueprint_id}"
            )
        
        # Check access
        user_team_id = current_user.get("team_id")
        user_roles = current_user.get("roles", [])
        
        if not check_blueprint_access(blueprint, current_user["user_id"], user_roles, user_team_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this Blueprint"
            )
        
        return blueprint
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get blueprint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get blueprint: {str(e)}"
        )


@router.put("/{blueprint_id}", response_model=BlueprintResponse)
async def update_blueprint(
    blueprint_id: str,
    request: UpdateBlueprintRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.BLUEPRINT_UPDATE)),
):
    """Update a Blueprint (creates new version).
    
    Updates a Blueprint by creating a new version. Previous versions are preserved.
    
    Validates: Requirements 2.3 (Version immutability)
    
    Args:
        blueprint_id: Blueprint ID
        request: Blueprint update request
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated Blueprint details (new version)
        
    Raises:
        HTTPException: If Blueprint not found, access denied, or update fails
    """
    try:
        # Get existing blueprint
        existing = db.query(Blueprint).filter(Blueprint.id == blueprint_id).first()
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Blueprint not found: {blueprint_id}"
            )
        
        # Check access
        user_team_id = current_user.get("team_id")
        user_roles = current_user.get("roles", [])
        
        if not check_blueprint_access(existing, current_user["user_id"], user_roles, user_team_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this Blueprint"
            )
        
        # Check if user is creator or team lead/admin
        if existing.created_by != current_user["user_id"] and "team_lead" not in user_roles and "admin" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the creator, team leads, or admins can update this Blueprint"
            )
        
        # Calculate new version (increment minor version)
        version_parts = existing.version.split(".")
        major, minor, patch = int(version_parts[0]), int(version_parts[1]), int(version_parts[2])
        new_version = f"{major}.{minor + 1}.{patch}"
        
        # Create new version (preserving old version)
        new_blueprint = Blueprint(
            id=f"bp-{uuid4().hex[:12]}",
            name=existing.name,
            description=request.description if request.description is not None else existing.description,
            version=new_version,
            operating_system=existing.operating_system,
            team_id=existing.team_id,
            bundle_image_id=request.bundle_image_id if request.bundle_image_id is not None else existing.bundle_image_id,
            software_manifest=request.software_manifest if request.software_manifest is not None else existing.software_manifest,
            configuration=request.configuration if request.configuration is not None else existing.configuration,
            created_by=current_user["user_id"],
            created_at=datetime.utcnow(),
            is_active=request.is_active if request.is_active is not None else True,
            is_public=request.is_public if request.is_public is not None else existing.is_public,
        )
        
        # Deactivate old version if new version is active
        if new_blueprint.is_active:
            existing.is_active = False
            existing.updated_at = datetime.utcnow()
        
        db.add(new_blueprint)
        db.commit()
        db.refresh(new_blueprint)
        
        logger.info(
            "blueprint_updated",
            blueprint_id=new_blueprint.id,
            name=new_blueprint.name,
            old_version=existing.version,
            new_version=new_blueprint.version,
            updated_by=current_user["user_id"],
        )
        
        return new_blueprint
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update blueprint: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update blueprint: {str(e)}"
        )

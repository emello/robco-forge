"""Audit log API routes.

Requirements:
- 10.1: Audit log access
- 10.2: Audit log search and export
- 10.3: Audit log integrity verification
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import Permission
from ..api.auth_routes import get_current_user, require_permission
from ..database import get_db
from ..models.audit_log import AuditLog
from ..audit.audit_logger import verify_audit_chain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


# Response models
class AuditLogResponse(BaseModel):
    """Audit log entry response."""
    id: str
    timestamp: datetime
    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    result: str
    error_message: Optional[str]
    source_ip: Optional[str]
    user_agent: Optional[str]
    interface: Optional[str]
    workspace_id: Optional[str]
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """List of audit logs response."""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


class AuditVerificationResponse(BaseModel):
    """Audit log chain verification response."""
    status: str
    message: str
    verified_count: int
    total_count: Optional[int] = None
    tampered_entries: Optional[List[Dict[str, Any]]] = None


# Routes
@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    result: Optional[str] = Query(None, description="Filter by result (SUCCESS, FAILURE, DENIED)"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.AUDIT_READ)),
):
    """List audit logs.
    
    Returns a paginated list of audit log entries with optional filters.
    
    Validates: Requirements 10.1
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        user_id: Optional user filter
        action: Optional action filter
        resource_type: Optional resource type filter
        result: Optional result filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Paginated list of audit logs
    """
    try:
        # Build query
        query = db.query(AuditLog)
        
        # Apply filters
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if result:
            query = query.filter(AuditLog.result == result)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        # Order by timestamp descending (most recent first)
        query = query.order_by(AuditLog.timestamp.desc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        logs = query.offset(offset).limit(page_size).all()
        
        return AuditLogListResponse(
            logs=logs,
            total=total,
            page=page,
            page_size=page_size,
        )
        
    except Exception as e:
        logger.error(f"Failed to list audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list audit logs: {str(e)}"
        )


@router.get("/{audit_id}", response_model=AuditLogResponse)
async def get_audit_log(
    audit_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.AUDIT_READ)),
):
    """Get audit log entry details.
    
    Returns detailed information about a specific audit log entry.
    
    Args:
        audit_id: Audit log ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Audit log entry details
        
    Raises:
        HTTPException: If audit log not found
    """
    try:
        log = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
        
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit log not found: {audit_id}"
            )
        
        return log
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit log: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit log: {str(e)}"
        )


@router.post("/verify", response_model=AuditVerificationResponse)
async def verify_audit_logs(
    limit: int = Query(100, ge=1, le=1000, description="Number of recent entries to verify"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.AUDIT_READ)),
):
    """Verify audit log chain integrity.
    
    Verifies that the audit log chain has not been tampered with by checking
    the hash chain of recent entries.
    
    Validates: Requirements 10.3
    
    Args:
        limit: Number of recent entries to verify
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Verification result
    """
    try:
        result = verify_audit_chain(db, limit)
        
        return AuditVerificationResponse(
            status=result["status"],
            message=result["message"],
            verified_count=result.get("verified_count", 0),
            total_count=result.get("total_count"),
            tampered_entries=result.get("tampered_entries"),
        )
        
    except Exception as e:
        logger.error(f"Failed to verify audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify audit logs: {str(e)}"
        )


@router.get("/export/csv")
async def export_audit_logs_csv(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.AUDIT_EXPORT)),
):
    """Export audit logs to CSV.
    
    Exports audit logs for the specified period in CSV format.
    
    Validates: Requirements 10.2
    
    Note: Full CSV export implementation will be added later.
    
    Args:
        start_date: Optional start date
        end_date: Optional end date
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        CSV file
    """
    # TODO: Implement CSV export
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="CSV export not yet implemented"
    )

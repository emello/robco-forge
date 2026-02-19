"""Cost management API routes.

Requirements:
- 11.1: Real-time cost tracking
- 11.2: Cost aggregation by team, project, user
- 13.5: Cost optimization recommendations
- 16.1: Cost report generation
- 16.2: Cost report breakdown

Note: This is a simplified implementation. Full Cost Engine will be implemented in Task 17-20.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..auth import Permission
from ..api.auth_routes import get_current_user, require_permission
from ..database import get_db
from ..models.cost_record import CostRecord
from ..models.workspace import WorkSpace

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/costs", tags=["costs"])


# Request/Response models
class CostPeriod(BaseModel):
    """Cost period model."""
    start: datetime
    end: datetime


class CostBreakdown(BaseModel):
    """Cost breakdown model."""
    compute: float
    storage: float
    data_transfer: float


class CostByWorkSpace(BaseModel):
    """Cost by WorkSpace model."""
    workspace_id: str
    workspace_name: Optional[str]
    cost: float


class CostByTeam(BaseModel):
    """Cost by team model."""
    team_id: str
    cost: float


class CostDataResponse(BaseModel):
    """Cost data response."""
    period: CostPeriod
    total_cost: float
    breakdown: CostBreakdown
    by_workspace: List[CostByWorkSpace]
    by_team: List[CostByTeam]


class CostRecommendation(BaseModel):
    """Cost optimization recommendation."""
    workspace_id: str
    workspace_name: Optional[str]
    recommendation_type: str  # "downgrade", "upgrade", "billing_mode", "terminate_stale"
    current_state: Dict[str, Any]
    recommended_state: Dict[str, Any]
    estimated_savings: float  # Negative for cost increases
    reason: str


class CostRecommendationsResponse(BaseModel):
    """Cost recommendations response."""
    recommendations: List[CostRecommendation]
    total_potential_savings: float


class CostReportResponse(BaseModel):
    """Cost report response."""
    report_id: str
    period: CostPeriod
    generated_at: datetime
    total_cost: float
    breakdown: CostBreakdown
    by_team: List[CostByTeam]
    by_workspace: List[CostByWorkSpace]
    format: str  # "json", "csv", "pdf"


# Routes
@router.get("", response_model=CostDataResponse)
async def get_costs(
    start_date: Optional[datetime] = Query(None, description="Start date (defaults to beginning of current month)"),
    end_date: Optional[datetime] = Query(None, description="End date (defaults to now)"),
    team_id: Optional[str] = Query(None, description="Filter by team"),
    workspace_id: Optional[str] = Query(None, description="Filter by workspace"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get cost data.
    
    Returns cost data for the specified period, aggregated by workspace and team.
    
    Validates: Requirements 11.1, 11.2
    
    Args:
        start_date: Start date for cost query
        end_date: End date for cost query
        team_id: Optional team filter
        workspace_id: Optional workspace filter
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Cost data with breakdowns
    """
    try:
        # Default to current month if no dates provided
        if not start_date:
            now = datetime.utcnow()
            start_date = datetime(now.year, now.month, 1)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Check permissions
        user_roles = current_user.get("roles", [])
        user_team_id = current_user.get("team_id")
        
        # Build query
        query = db.query(CostRecord).filter(
            CostRecord.period_start >= start_date,
            CostRecord.period_end <= end_date
        )
        
        # Apply filters based on permissions
        if "admin" in user_roles:
            # Admin can see all costs
            pass
        elif "team_lead" in user_roles:
            # Team lead can see team costs
            if team_id:
                query = query.filter(CostRecord.team_id == team_id)
            else:
                query = query.filter(CostRecord.team_id == user_team_id)
        else:
            # Regular users can only see their own costs
            query = query.filter(CostRecord.user_id == current_user["user_id"])
        
        # Apply workspace filter if provided
        if workspace_id:
            query = query.filter(CostRecord.workspace_id == workspace_id)
        
        # Get cost records
        cost_records = query.all()
        
        # Calculate totals
        total_compute = sum(r.compute_cost for r in cost_records)
        total_storage = sum(r.storage_cost for r in cost_records)
        total_transfer = sum(r.data_transfer_cost for r in cost_records)
        total_cost = sum(r.total_cost for r in cost_records)
        
        # Aggregate by workspace
        workspace_costs: Dict[str, float] = {}
        for record in cost_records:
            workspace_costs[record.workspace_id] = workspace_costs.get(record.workspace_id, 0) + record.total_cost
        
        by_workspace = [
            CostByWorkSpace(workspace_id=ws_id, workspace_name=None, cost=cost)
            for ws_id, cost in workspace_costs.items()
        ]
        
        # Aggregate by team
        team_costs: Dict[str, float] = {}
        for record in cost_records:
            team_costs[record.team_id] = team_costs.get(record.team_id, 0) + record.total_cost
        
        by_team = [
            CostByTeam(team_id=t_id, cost=cost)
            for t_id, cost in team_costs.items()
        ]
        
        return CostDataResponse(
            period=CostPeriod(start=start_date, end=end_date),
            total_cost=total_cost,
            breakdown=CostBreakdown(
                compute=total_compute,
                storage=total_storage,
                data_transfer=total_transfer
            ),
            by_workspace=by_workspace,
            by_team=by_team,
        )
        
    except Exception as e:
        logger.error(f"Failed to get costs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get costs: {str(e)}"
        )


@router.get("/recommendations", response_model=CostRecommendationsResponse)
async def get_cost_recommendations(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get cost optimization recommendations.
    
    Returns recommendations for reducing costs based on usage patterns.
    
    Validates: Requirements 13.2, 13.3, 13.4, 13.5
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Cost optimization recommendations
    """
    try:
        from ..cost.utilization_analyzer import UtilizationAnalyzer
        
        # Get user's workspaces
        workspaces = db.query(WorkSpace).filter(
            WorkSpace.user_id == current_user["user_id"]
        ).all()
        
        # Convert to dict format for analyzer
        workspace_list = [
            {"id": ws.id, "bundle_type": ws.bundle_type}
            for ws in workspaces
        ]
        
        # Generate recommendations using UtilizationAnalyzer
        analyzer = UtilizationAnalyzer()
        raw_recommendations = analyzer.get_recommendations_for_workspaces(workspace_list)
        
        # Convert to API response format
        recommendations = []
        for rec in raw_recommendations:
            # Determine recommendation type
            rec_type = "downgrade" if rec["reason"] == "low_utilization" else "upgrade"
            
            recommendations.append(CostRecommendation(
                workspace_id=rec["workspace_id"],
                workspace_name=None,  # TODO: Get from workspace model
                recommendation_type=rec_type,
                current_state={
                    "bundle_type": rec["current_bundle"],
                    "monthly_cost": rec["cost_impact"]["current_monthly_cost"],
                    "avg_cpu_percent": rec["utilization"]["avg_cpu_percent"],
                    "avg_memory_percent": rec["utilization"]["avg_memory_percent"]
                },
                recommended_state={
                    "bundle_type": rec["target_bundle"],
                    "monthly_cost": rec["cost_impact"]["target_monthly_cost"]
                },
                estimated_savings=rec["cost_impact"]["monthly_savings"],
                reason=f"Average CPU utilization is {rec['utilization']['avg_cpu_percent']:.1f}% over the past 14 days"
            ))
        
        total_savings = sum(r.estimated_savings for r in recommendations)
        
        logger.info(
            f"cost_recommendations_generated user_id={current_user['user_id']} "
            f"count={len(recommendations)} total_savings=${total_savings:.2f}"
        )
        
        return CostRecommendationsResponse(
            recommendations=recommendations,
            total_potential_savings=total_savings,
        )
        
    except Exception as e:
        logger.error(f"Failed to get cost recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cost recommendations: {str(e)}"
        )


@router.get("/reports", response_model=CostReportResponse)
async def generate_cost_report(
    start_date: Optional[datetime] = Query(None, description="Start date (defaults to beginning of current month)"),
    end_date: Optional[datetime] = Query(None, description="End date (defaults to now)"),
    format: str = Query("json", description="Report format (json, csv, pdf)"),
    team_id: Optional[str] = Query(None, description="Filter by team"),
    group_by: str = Query("team", description="Group by dimension (team, project, cost_center, user)"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission(Permission.COST_EXPORT)),
):
    """Generate cost report.
    
    Generates a detailed cost report for the specified period.
    
    Validates: Requirements 16.1, 16.2, 16.3
    
    Args:
        start_date: Start date for report
        end_date: End date for report
        format: Report format
        team_id: Optional team filter
        group_by: Grouping dimension
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Cost report
    """
    try:
        from ..cost.report_generator import CostReportGenerator
        
        # Validate format
        valid_formats = ["json", "csv", "pdf"]
        if format not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
            )
        
        # Validate group_by
        valid_groups = ["team", "project", "cost_center", "user"]
        if group_by not in valid_groups:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid group_by. Must be one of: {', '.join(valid_groups)}"
            )
        
        # Default to current month if no dates provided
        if not start_date:
            now = datetime.utcnow()
            start_date = datetime(now.year, now.month, 1)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Check permissions
        user_roles = current_user.get("roles", [])
        user_team_id = current_user.get("team_id")
        
        # Build query
        query = db.query(CostRecord).filter(
            CostRecord.period_start >= start_date,
            CostRecord.period_end <= end_date
        )
        
        # Apply filters based on permissions
        if "admin" in user_roles:
            # Admin can see all costs
            pass
        elif "team_lead" in user_roles:
            # Team lead can see team costs
            if team_id:
                query = query.filter(CostRecord.team_id == team_id)
            else:
                query = query.filter(CostRecord.team_id == user_team_id)
        else:
            # Regular users can only see their own costs
            query = query.filter(CostRecord.user_id == current_user["user_id"])
        
        # Apply team filter if provided
        if team_id and "admin" in user_roles:
            query = query.filter(CostRecord.team_id == team_id)
        
        # Get cost records
        cost_records = query.all()
        
        # Generate report
        generator = CostReportGenerator()
        report_data, csv_content, pdf_content = generator.generate_and_export(
            start_date=start_date,
            end_date=end_date,
            cost_records=cost_records,
            group_by=group_by,
            export_format=format
        )
        
        # For CSV and PDF, return as downloadable file
        if format == "csv" and csv_content:
            from fastapi.responses import Response
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=cost_report_{report_data['report_id']}.csv"
                }
            )
        elif format == "pdf" and pdf_content:
            from fastapi.responses import Response
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=cost_report_{report_data['report_id']}.pdf"
                }
            )
        
        # Return JSON response
        # Convert report_data to CostReportResponse format
        return CostReportResponse(
            report_id=report_data["report_id"],
            period=CostPeriod(
                start=datetime.fromisoformat(report_data["period"]["start"]),
                end=datetime.fromisoformat(report_data["period"]["end"])
            ),
            generated_at=datetime.fromisoformat(report_data["generated_at"]),
            total_cost=report_data["summary"]["total_cost"],
            breakdown=CostBreakdown(
                compute=report_data["summary"]["compute_cost"],
                storage=report_data["summary"]["storage_cost"],
                data_transfer=report_data["summary"]["data_transfer_cost"]
            ),
            by_team=[],  # Simplified for now
            by_workspace=[],  # Simplified for now
            format=format,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate cost report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cost report: {str(e)}"
        )

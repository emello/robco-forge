"""Cost and diagnostic tools for Lucy AI.

These tools call Forge API and Cost Engine endpoints.
Requirements: 5.6, 5.7
"""

from typing import Dict, Any, Optional
import httpx

from .tool_executor import Tool, ToolResult, ToolCategory


class GetCostSummaryTool(Tool):
    """Tool for getting cost summary.
    
    Calls Forge API GET /api/v1/costs endpoint.
    Requirements: 5.6
    """
    
    def __init__(self, api_base_url: str):
        """Initialize get cost summary tool.
        
        Args:
            api_base_url: Base URL for Forge API
        """
        super().__init__(
            name="get_cost_summary",
            category=ToolCategory.COST_QUERY,
            description=(
                "Get cost summary for the user or team. "
                "Shows total costs, breakdown by workspace, and cost trends. "
                "Supports filtering by time period."
            )
        )
        self.api_base_url = api_base_url
    
    async def execute(self, user_id: str, **kwargs) -> ToolResult:
        """Execute cost summary query.
        
        Args:
            user_id: User requesting the summary
            **kwargs: Optional filters (period, team_id, project_id)
            
        Returns:
            ToolResult with cost summary data
        """
        # Build query parameters
        params = {}
        
        period = kwargs.get("period", "current_month")
        if period:
            params["period"] = period
        
        team_id = kwargs.get("team_id")
        if team_id:
            params["team_id"] = team_id
        
        project_id = kwargs.get("project_id")
        if project_id:
            params["project_id"] = project_id
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/costs",
                    params=params,
                    headers={"X-User-ID": user_id},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    return ToolResult(
                        success=True,
                        data={
                            "period": data.get("period"),
                            "total_cost": data.get("total_cost"),
                            "breakdown": data.get("breakdown"),
                            "by_workspace": data.get("by_workspace", []),
                            "by_team": data.get("by_team", [])
                        }
                    )
                elif response.status_code == 403:
                    return ToolResult(
                        success=False,
                        error="Permission denied: You don't have access to this cost data"
                    )
                else:
                    error_data = response.json()
                    return ToolResult(
                        success=False,
                        error=f"Failed to get cost summary: {error_data.get('detail', 'Unknown error')}"
                    )
                    
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get cost summary: {str(e)}"
            )
    
    def _get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for cost summary."""
        return {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["current_month", "last_month", "last_7_days", "last_30_days", "custom"],
                    "description": "Time period for cost summary",
                    "default": "current_month"
                },
                "team_id": {
                    "type": "string",
                    "description": "Optional team ID to filter costs"
                },
                "project_id": {
                    "type": "string",
                    "description": "Optional project ID to filter costs"
                }
            },
            "required": []
        }


class GetCostRecommendationsTool(Tool):
    """Tool for getting cost optimization recommendations.
    
    Calls Forge API GET /api/v1/costs/recommendations endpoint.
    Requirements: 5.6
    """
    
    def __init__(self, api_base_url: str):
        """Initialize get cost recommendations tool.
        
        Args:
            api_base_url: Base URL for Forge API
        """
        super().__init__(
            name="get_cost_recommendations",
            category=ToolCategory.COST_QUERY,
            description=(
                "Get cost optimization recommendations for workspaces. "
                "Includes right-sizing suggestions, billing mode recommendations, "
                "and estimated cost savings."
            )
        )
        self.api_base_url = api_base_url
    
    async def execute(self, user_id: str, **kwargs) -> ToolResult:
        """Execute cost recommendations query.
        
        Args:
            user_id: User requesting recommendations
            **kwargs: Optional filters
            
        Returns:
            ToolResult with recommendations
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/costs/recommendations",
                    headers={"X-User-ID": user_id},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    recommendations = data.get("recommendations", [])
                    
                    # Calculate total potential savings
                    total_savings = sum(
                        rec.get("estimated_savings", 0)
                        for rec in recommendations
                        if rec.get("estimated_savings", 0) > 0
                    )
                    
                    return ToolResult(
                        success=True,
                        data={
                            "count": len(recommendations),
                            "total_potential_savings": total_savings,
                            "recommendations": recommendations
                        }
                    )
                elif response.status_code == 403:
                    return ToolResult(
                        success=False,
                        error="Permission denied: You don't have access to recommendations"
                    )
                else:
                    error_data = response.json()
                    return ToolResult(
                        success=False,
                        error=f"Failed to get recommendations: {error_data.get('detail', 'Unknown error')}"
                    )
                    
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get recommendations: {str(e)}"
            )
    
    def _get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for recommendations."""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }


class CheckBudgetTool(Tool):
    """Tool for checking budget status.
    
    Calls Forge API GET /api/v1/budgets endpoint.
    Requirements: 5.6
    """
    
    def __init__(self, api_base_url: str):
        """Initialize check budget tool.
        
        Args:
            api_base_url: Base URL for Forge API
        """
        super().__init__(
            name="check_budget",
            category=ToolCategory.COST_QUERY,
            description=(
                "Check budget status for user, team, or project. "
                "Shows current spending, budget limit, and percentage used. "
                "Warns if approaching or exceeding budget limits."
            )
        )
        self.api_base_url = api_base_url
    
    async def execute(self, user_id: str, **kwargs) -> ToolResult:
        """Execute budget check.
        
        Args:
            user_id: User requesting budget check
            **kwargs: Optional scope (team_id, project_id)
            
        Returns:
            ToolResult with budget status
        """
        # Build query parameters
        params = {}
        
        team_id = kwargs.get("team_id")
        if team_id:
            params["team_id"] = team_id
        
        project_id = kwargs.get("project_id")
        if project_id:
            params["project_id"] = project_id
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/budgets/status",
                    params=params,
                    headers={"X-User-ID": user_id},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    budget = data.get("budget", 0)
                    current_spend = data.get("current_spend", 0)
                    percentage_used = data.get("percentage_used", 0)
                    
                    # Determine warning level
                    warning = None
                    if percentage_used >= 100:
                        warning = "⚠️ BUDGET EXCEEDED: No new workspaces can be provisioned"
                    elif percentage_used >= 80:
                        warning = "⚠️ WARNING: 80% of budget used"
                    
                    return ToolResult(
                        success=True,
                        data={
                            "budget": budget,
                            "current_spend": current_spend,
                            "remaining": budget - current_spend,
                            "percentage_used": percentage_used,
                            "warning": warning,
                            "scope": data.get("scope", "user")
                        }
                    )
                elif response.status_code == 403:
                    return ToolResult(
                        success=False,
                        error="Permission denied: You don't have access to this budget data"
                    )
                else:
                    error_data = response.json()
                    return ToolResult(
                        success=False,
                        error=f"Failed to check budget: {error_data.get('detail', 'Unknown error')}"
                    )
                    
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to check budget: {str(e)}"
            )
    
    def _get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for budget check."""
        return {
            "type": "object",
            "properties": {
                "team_id": {
                    "type": "string",
                    "description": "Optional team ID to check team budget"
                },
                "project_id": {
                    "type": "string",
                    "description": "Optional project ID to check project budget"
                }
            },
            "required": []
        }


class RunDiagnosticsTool(Tool):
    """Tool for running workspace diagnostics.
    
    Calls Forge API POST /api/v1/workspaces/{id}/diagnostics endpoint.
    Requirements: 5.7
    """
    
    def __init__(self, api_base_url: str):
        """Initialize run diagnostics tool.
        
        Args:
            api_base_url: Base URL for Forge API
        """
        super().__init__(
            name="run_diagnostics",
            category=ToolCategory.DIAGNOSTICS,
            description=(
                "Run diagnostic checks on a workspace. "
                "Checks connectivity, performance, configuration, and health status. "
                "Provides troubleshooting recommendations."
            )
        )
        self.api_base_url = api_base_url
    
    async def execute(self, user_id: str, **kwargs) -> ToolResult:
        """Execute diagnostics.
        
        Args:
            user_id: User requesting diagnostics
            **kwargs: Must include workspace_id
            
        Returns:
            ToolResult with diagnostic results
        """
        workspace_id = kwargs.get("workspace_id")
        
        if not workspace_id:
            return ToolResult(
                success=False,
                error="workspace_id is required"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/workspaces/{workspace_id}/diagnostics",
                    headers={"X-User-ID": user_id},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    checks = data.get("checks", [])
                    failed_checks = [c for c in checks if not c.get("passed", True)]
                    
                    return ToolResult(
                        success=True,
                        data={
                            "workspace_id": workspace_id,
                            "overall_status": data.get("overall_status", "unknown"),
                            "checks": checks,
                            "failed_count": len(failed_checks),
                            "recommendations": data.get("recommendations", [])
                        }
                    )
                elif response.status_code == 404:
                    return ToolResult(
                        success=False,
                        error=f"WorkSpace {workspace_id} not found"
                    )
                elif response.status_code == 403:
                    return ToolResult(
                        success=False,
                        error="Permission denied: You don't own this workspace"
                    )
                else:
                    error_data = response.json()
                    return ToolResult(
                        success=False,
                        error=f"Failed to run diagnostics: {error_data.get('detail', 'Unknown error')}"
                    )
                    
        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                error="Diagnostics timed out. The workspace may be unresponsive."
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to run diagnostics: {str(e)}"
            )
    
    def _get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for diagnostics."""
        return {
            "type": "object",
            "properties": {
                "workspace_id": {
                    "type": "string",
                    "description": "ID of the workspace to diagnose"
                }
            },
            "required": ["workspace_id"]
        }

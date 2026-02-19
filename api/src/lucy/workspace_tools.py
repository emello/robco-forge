"""Workspace management tools for Lucy AI.

These tools call Forge API endpoints to manage WorkSpaces.
Requirements: 5.4, 5.5
"""

from typing import Dict, Any, Optional, List
import httpx

from .tool_executor import Tool, ToolResult, ToolCategory, ConfirmationRequired


class ProvisionWorkspaceTool(Tool):
    """Tool for provisioning new WorkSpaces.
    
    Calls Forge API POST /api/v1/workspaces endpoint.
    Rate limited: 5 provisions per user per hour.
    Requirements: 5.4
    """
    
    def __init__(self, api_base_url: str):
        """Initialize provision workspace tool.
        
        Args:
            api_base_url: Base URL for Forge API
        """
        super().__init__(
            name="provision_workspace",
            category=ToolCategory.PROVISIONING,
            description=(
                "Provision a new AWS WorkSpace for the user. "
                "Requires bundle type and blueprint ID. "
                "Returns workspace details including ID and connection URL."
            )
        )
        self.api_base_url = api_base_url
    
    async def execute(self, user_id: str, **kwargs) -> ToolResult:
        """Execute workspace provisioning.
        
        Args:
            user_id: User requesting the workspace
            **kwargs: Provisioning parameters (bundle_type, blueprint_id, tags, etc.)
            
        Returns:
            ToolResult with workspace details or error
        """
        # Extract parameters
        bundle_type = kwargs.get("bundle_type")
        blueprint_id = kwargs.get("blueprint_id")
        tags = kwargs.get("tags", {})
        auto_stop_timeout_minutes = kwargs.get("auto_stop_timeout_minutes")
        max_lifetime_days = kwargs.get("max_lifetime_days")
        
        if not bundle_type:
            return ToolResult(
                success=False,
                error="bundle_type is required"
            )
        
        if not blueprint_id:
            return ToolResult(
                success=False,
                error="blueprint_id is required"
            )
        
        # Build request payload
        payload = {
            "service_type": "WORKSPACES_PERSONAL",
            "bundle_type": bundle_type,
            "operating_system": "LINUX",  # Default to Linux
            "blueprint_id": blueprint_id,
            "tags": tags
        }
        
        if auto_stop_timeout_minutes:
            payload["auto_stop_timeout_minutes"] = auto_stop_timeout_minutes
        
        if max_lifetime_days:
            payload["max_lifetime_days"] = max_lifetime_days
        
        # Call Forge API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/workspaces",
                    json=payload,
                    headers={"X-User-ID": user_id},
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    workspace = response.json()
                    return ToolResult(
                        success=True,
                        data={
                            "workspace_id": workspace.get("id"),
                            "state": workspace.get("state"),
                            "region": workspace.get("region"),
                            "connection_url": workspace.get("connection_url"),
                            "message": f"WorkSpace {workspace.get('id')} is being provisioned"
                        }
                    )
                elif response.status_code == 402:
                    # Budget exceeded
                    error_data = response.json()
                    return ToolResult(
                        success=False,
                        error=f"Budget exceeded: {error_data.get('detail', 'Cannot provision workspace')}"
                    )
                elif response.status_code == 403:
                    return ToolResult(
                        success=False,
                        error="Permission denied: You don't have access to this bundle type"
                    )
                else:
                    error_data = response.json()
                    return ToolResult(
                        success=False,
                        error=f"Provisioning failed: {error_data.get('detail', 'Unknown error')}"
                    )
                    
        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                error="Request timed out. Please try again."
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to provision workspace: {str(e)}"
            )
    
    def _get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for provisioning."""
        return {
            "type": "object",
            "properties": {
                "bundle_type": {
                    "type": "string",
                    "enum": ["STANDARD", "PERFORMANCE", "POWER", "POWERPRO", "GRAPHICS_G4DN", "GRAPHICSPRO_G4DN"],
                    "description": "WorkSpace hardware configuration"
                },
                "blueprint_id": {
                    "type": "string",
                    "description": "Blueprint ID for the workspace environment"
                },
                "tags": {
                    "type": "object",
                    "description": "Optional cost allocation tags",
                    "additionalProperties": {"type": "string"}
                },
                "auto_stop_timeout_minutes": {
                    "type": "integer",
                    "description": "Optional idle timeout in minutes"
                },
                "max_lifetime_days": {
                    "type": "integer",
                    "description": "Optional maximum lifetime in days"
                }
            },
            "required": ["bundle_type", "blueprint_id"]
        }


class ListWorkspacesTool(Tool):
    """Tool for listing user's WorkSpaces.
    
    Calls Forge API GET /api/v1/workspaces endpoint.
    Requirements: 5.5
    """
    
    def __init__(self, api_base_url: str):
        """Initialize list workspaces tool.
        
        Args:
            api_base_url: Base URL for Forge API
        """
        super().__init__(
            name="list_workspaces",
            category=ToolCategory.WORKSPACE_MANAGEMENT,
            description="List all WorkSpaces owned by the user with their current state and details."
        )
        self.api_base_url = api_base_url
    
    async def execute(self, user_id: str, **kwargs) -> ToolResult:
        """Execute workspace listing.
        
        Args:
            user_id: User requesting the list
            **kwargs: Optional filters
            
        Returns:
            ToolResult with list of workspaces
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/workspaces",
                    headers={"X-User-ID": user_id},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    workspaces = data.get("workspaces", [])
                    
                    return ToolResult(
                        success=True,
                        data={
                            "count": len(workspaces),
                            "workspaces": workspaces
                        }
                    )
                else:
                    error_data = response.json()
                    return ToolResult(
                        success=False,
                        error=f"Failed to list workspaces: {error_data.get('detail', 'Unknown error')}"
                    )
                    
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to list workspaces: {str(e)}"
            )
    
    def _get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for listing."""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }


class StartWorkspaceTool(Tool):
    """Tool for starting a stopped WorkSpace.
    
    Calls Forge API POST /api/v1/workspaces/{id}/start endpoint.
    Requirements: 5.5
    """
    
    def __init__(self, api_base_url: str):
        """Initialize start workspace tool.
        
        Args:
            api_base_url: Base URL for Forge API
        """
        super().__init__(
            name="start_workspace",
            category=ToolCategory.WORKSPACE_MANAGEMENT,
            description="Start a stopped WorkSpace. The workspace must be in STOPPED state."
        )
        self.api_base_url = api_base_url
    
    async def execute(self, user_id: str, **kwargs) -> ToolResult:
        """Execute workspace start.
        
        Args:
            user_id: User requesting the action
            **kwargs: Must include workspace_id
            
        Returns:
            ToolResult with action result
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
                    f"{self.api_base_url}/api/v1/workspaces/{workspace_id}/start",
                    headers={"X-User-ID": user_id},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return ToolResult(
                        success=True,
                        data={
                            "workspace_id": workspace_id,
                            "message": data.get("message", "WorkSpace is starting")
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
                        error=f"Failed to start workspace: {error_data.get('detail', 'Unknown error')}"
                    )
                    
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to start workspace: {str(e)}"
            )
    
    def _get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for starting."""
        return {
            "type": "object",
            "properties": {
                "workspace_id": {
                    "type": "string",
                    "description": "ID of the workspace to start"
                }
            },
            "required": ["workspace_id"]
        }


class StopWorkspaceTool(Tool):
    """Tool for stopping a running WorkSpace.
    
    Calls Forge API POST /api/v1/workspaces/{id}/stop endpoint.
    Requires user confirmation before execution.
    Requirements: 5.5
    """
    
    def __init__(self, api_base_url: str):
        """Initialize stop workspace tool.
        
        Args:
            api_base_url: Base URL for Forge API
        """
        super().__init__(
            name="stop_workspace",
            category=ToolCategory.WORKSPACE_MANAGEMENT,
            description=(
                "Stop a running WorkSpace. This will disconnect any active sessions. "
                "Requires user confirmation."
            )
        )
        self.api_base_url = api_base_url
    
    async def execute(self, user_id: str, **kwargs) -> ToolResult:
        """Execute workspace stop.
        
        Args:
            user_id: User requesting the action
            **kwargs: Must include workspace_id, optionally confirmed
            
        Returns:
            ToolResult with action result or confirmation request
        """
        workspace_id = kwargs.get("workspace_id")
        confirmed = kwargs.get("confirmed", False)
        
        if not workspace_id:
            return ToolResult(
                success=False,
                error="workspace_id is required"
            )
        
        # Require confirmation for destructive action
        if not confirmed:
            return ToolResult(
                success=False,
                requires_confirmation=True,
                confirmation_message=(
                    f"Are you sure you want to stop WorkSpace {workspace_id}? "
                    "This will disconnect any active sessions."
                )
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/workspaces/{workspace_id}/stop",
                    headers={"X-User-ID": user_id},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return ToolResult(
                        success=True,
                        data={
                            "workspace_id": workspace_id,
                            "message": data.get("message", "WorkSpace is stopping")
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
                        error=f"Failed to stop workspace: {error_data.get('detail', 'Unknown error')}"
                    )
                    
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to stop workspace: {str(e)}"
            )
    
    def _get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for stopping."""
        return {
            "type": "object",
            "properties": {
                "workspace_id": {
                    "type": "string",
                    "description": "ID of the workspace to stop"
                },
                "confirmed": {
                    "type": "boolean",
                    "description": "Confirmation flag (set to true after user confirms)"
                }
            },
            "required": ["workspace_id"]
        }


class TerminateWorkspaceTool(Tool):
    """Tool for terminating a WorkSpace.
    
    Calls Forge API DELETE /api/v1/workspaces/{id} endpoint.
    DESTRUCTIVE: Always requires user confirmation.
    Requirements: 5.5
    """
    
    def __init__(self, api_base_url: str):
        """Initialize terminate workspace tool.
        
        Args:
            api_base_url: Base URL for Forge API
        """
        super().__init__(
            name="terminate_workspace",
            category=ToolCategory.WORKSPACE_MANAGEMENT,
            description=(
                "Permanently terminate a WorkSpace. This action cannot be undone. "
                "All data on the workspace will be lost. User volumes are preserved. "
                "ALWAYS requires user confirmation."
            )
        )
        self.api_base_url = api_base_url
    
    async def execute(self, user_id: str, **kwargs) -> ToolResult:
        """Execute workspace termination.
        
        Args:
            user_id: User requesting the action
            **kwargs: Must include workspace_id, optionally confirmed
            
        Returns:
            ToolResult with action result or confirmation request
        """
        workspace_id = kwargs.get("workspace_id")
        confirmed = kwargs.get("confirmed", False)
        
        if not workspace_id:
            return ToolResult(
                success=False,
                error="workspace_id is required"
            )
        
        # ALWAYS require confirmation for termination
        if not confirmed:
            return ToolResult(
                success=False,
                requires_confirmation=True,
                confirmation_message=(
                    f"⚠️ WARNING: Are you sure you want to TERMINATE WorkSpace {workspace_id}? "
                    "This action CANNOT be undone. All data on the workspace will be permanently lost. "
                    "User volumes will be preserved."
                )
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.api_base_url}/api/v1/workspaces/{workspace_id}",
                    headers={"X-User-ID": user_id},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return ToolResult(
                        success=True,
                        data={
                            "workspace_id": workspace_id,
                            "message": data.get("message", "WorkSpace is being terminated")
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
                        error=f"Failed to terminate workspace: {error_data.get('detail', 'Unknown error')}"
                    )
                    
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to terminate workspace: {str(e)}"
            )
    
    def _get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for termination."""
        return {
            "type": "object",
            "properties": {
                "workspace_id": {
                    "type": "string",
                    "description": "ID of the workspace to terminate"
                },
                "confirmed": {
                    "type": "boolean",
                    "description": "Confirmation flag (MUST be true to proceed)"
                }
            },
            "required": ["workspace_id"]
        }
